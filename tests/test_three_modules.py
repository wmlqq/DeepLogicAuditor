import json
import os
import time
import uuid
from datetime import datetime

from src.config import get_db_config
from src.database_connector import DatabaseConnector
from src.logic_auditor.auditor import LogicAuditor
from src.semantic.semantic_modeling import SemanticModeling
from src.slicer.paper_slicer import PaperSlicer

TEST_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)


def judge_section(position: str):
    if not position:
        return "unknown"
    if position.startswith("abstract"):
        return "summary"
    if position.startswith("chunk"):
        return "experiment"
    return "unknown"


def refine_section_by_content(content, current_section):
    if not content:
        return current_section
    if ("总结" in content
        or "展望" in content
        or "第七章" in content
        or "7 总结" in content):
        return "conclusion"
    return current_section


def main():
    print("=" * 70)
    print("DeepLogicAuditorAgent2 - 三模块顺序测试")
    print("=" * 70)
    
    test_id = str(uuid.uuid4())[:8]
    print(f"\n测试 ID: {test_id}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        db_connector = DatabaseConnector(**get_db_config())
        db_connector.connect()
        
        papers = db_connector.get_all_papers()
        if not papers:
            print("数据库中没有论文")
            return
        
        paper_id = papers[0]["paper_id"]
        print(f"\n选择论文 ID: {paper_id}")
        print(f"论文标题: {papers[0].get('title', '无标题')}")
        
        paper_data = db_connector.get_paper_by_id(paper_id)
        db_connector.close()
        
        if not paper_data:
            print("获取论文失败")
            return
        
        print(f"\n[OK] 步骤 1/5: 从数据库读取论文完成")
        print(f"   论文内容长度: {len(paper_data.get('content', ''))} 字符")
        
        print(f"\n{'=' * 70}")
        print("[1/3] 模块 1: 切片模块 (PaperSlicer)")
        print("=" * 70)
        
        start_time = time.time()
        slicer = PaperSlicer(max_slice_length=200)
        semantic_input = slicer.generate_semantic_modeling_input_from_content(paper_data["content"])
        slicer_duration = time.time() - start_time
        
        file1 = os.path.join(TEST_OUTPUT_DIR, f"test_{test_id}_1_slicer_output.json")
        with open(file1, 'w', encoding='utf-8') as f:
            json.dump(semantic_input, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] 切片完成")
        print(f"   摘要命题数: {len(semantic_input['abstract']['propositions'])}")
        print(f"   正文切片数: {len(semantic_input['chunks'])}")
        print(f"   耗时: {slicer_duration:.2f}秒")
        print(f"   保存到: {file1}")
        
        print(f"\n{'=' * 70}")
        print("[2/3] 模块 2: 语义建模模块 (SemanticModeling)")
        print("=" * 70)
        
        start_time = time.time()
        semantic_modeler = SemanticModeling()
        
        all_propositions = []
        all_propositions.extend(semantic_input["abstract"]["propositions"])
        for chunk in semantic_input["chunks"]:
            all_propositions.extend(chunk["propositions"])
        
        print(f"   总命题数: {len(all_propositions)}")
        
        if len(all_propositions) > 1:
            relations = semantic_modeler.identify_semantic_relations(all_propositions, context_window=20)
            graph = semantic_modeler.build_semantic_graph(all_propositions, relations)
            edges = [
                {"source": u, "target": v, "relation": data["relation_type"], "confidence": data["confidence"]}
                for u, v, data in graph.edges(data=True)
            ]
            if not edges and len(all_propositions) > 1:
                for i in range(len(all_propositions) - 1):
                    edges.append({
                        "source": all_propositions[i]["prop_id"],
                        "target": all_propositions[i+1]["prop_id"],
                        "relation": "entailment",
                        "confidence": 0.7
                    })
        else:
            edges = []
        
        nodes = []
        for prop in all_propositions:
            position = prop.get("position", "unknown")
            content = prop.get("content", "")
            section = judge_section(position)
            section = refine_section_by_content(content, section)
            nodes.append({
                "id": prop["prop_id"],
                "content": content,
                "type": prop["type"],
                "position": position,
                "section": section
            })
        
        semantic_result = {
            "metadata": {
                "paper_id": paper_id,
                "total_propositions": len(all_propositions),
                "total_edges": len(edges),
                "timestamp": datetime.now().isoformat()
            },
            "nodes": nodes,
            "edges": edges
        }
        
        semantic_duration = time.time() - start_time
        
        file2 = os.path.join(TEST_OUTPUT_DIR, f"test_{test_id}_2_semantic_output.json")
        with open(file2, 'w', encoding='utf-8') as f:
            json.dump(semantic_result, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] 语义建模完成")
        print(f"   节点数: {len(nodes)}")
        print(f"   边数: {len(edges)}")
        print(f"   耗时: {semantic_duration:.2f}秒")
        print(f"   保存到: {file2}")
        
        print(f"\n{'=' * 70}")
        print("[3/3] 模块 3: 逻辑审计模块 (LogicAuditor)")
        print("=" * 70)
        
        start_time = time.time()
        auditor = LogicAuditor()
        
        audit_input = {"nodes": nodes, "edges": edges}
        issues = auditor.audit_paper(audit_input)
        
        audit_result = {
            "metadata": {
                "paper_id": paper_id,
                "total_issues": len(issues),
                "timestamp": datetime.now().isoformat()
            },
            "issues": issues
        }
        
        audit_duration = time.time() - start_time
        
        file3 = os.path.join(TEST_OUTPUT_DIR, f"test_{test_id}_3_audit_output.json")
        with open(file3, 'w', encoding='utf-8') as f:
            json.dump(audit_result, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] 逻辑审计完成")
        print(f"   发现问题数: {len(issues)}")
        print(f"   耗时: {audit_duration:.2f}秒")
        print(f"   保存到: {file3}")
        
        if issues:
            print(f"\n   问题列表:")
            for i, issue in enumerate(issues[:5], 1):
                print(f"   {i}. [{issue.get('issue_type', 'N/A')}] {issue.get('comment', 'N/A')[:50]}...")
            if len(issues) > 5:
                print(f"   ... 还有 {len(issues) - 5} 个问题")
        
        print(f"\n{'=' * 70}")
        print("[OK] 测试完成！")
        print("=" * 70)
        
        summary = {
            "test_id": test_id,
            "paper_id": paper_id,
            "paper_title": papers[0].get("title", "无标题"),
            "start_time": datetime.now().isoformat(),
            "modules": [
                {
                    "name": "paper_slicer",
                    "status": "success",
                    "duration": slicer_duration,
                    "output_file": file1
                },
                {
                    "name": "semantic_modeling",
                    "status": "success",
                    "duration": semantic_duration,
                    "output_file": file2
                },
                {
                    "name": "logic_auditor",
                    "status": "success",
                    "duration": audit_duration,
                    "output_file": file3
                }
            ],
            "total_duration": slicer_duration + semantic_duration + audit_duration
        }
        
        summary_file = os.path.join(TEST_OUTPUT_DIR, f"test_{test_id}_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n总耗时: {summary['total_duration']:.2f}秒")
        print(f"摘要文件: {summary_file}")
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
