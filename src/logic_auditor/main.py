import json
import random
import re
import time
import uuid
from typing import Any, Dict, List, Optional

import psycopg2
from fastapi import FastAPI
from psycopg2.extras import RealDictCursor

from src.config import get_db_config, get_output_dir
from src.database_connector import DatabaseConnector
from src.semantic.semantic_modeling import SemanticModeling
from src.slicer.paper_slicer import PaperSlicer

from .auditor import LogicAuditor
from .schemas import AgentInfo, AuditRequest, AuditResponse, Detail, Result, Usage

app = FastAPI(title="Deep Logic Auditor Agent", version="1.0.0")
auditor = LogicAuditor()
semantic_modeler = SemanticModeling()
slicer = PaperSlicer(max_slice_length=200)


def get_rules_from_db(agent_code: str = 'LOG') -> List[Dict]:
    """从 main_rules 表获取指定智能体的规则"""
    conn = None
    try:
        conn = psycopg2.connect(**get_db_config(), cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("""
            SELECT rule_id, rule_name_cn, full_score, severity
            FROM main_rules
            WHERE agent_code = %s
        """, (agent_code,))
        rules = cur.fetchall()
        return rules
    except Exception as e:
        print(f"获取规则失败: {e}")
        return []
    finally:
        if conn:
            conn.close()


def safe_uuid(value: Any, default: Optional[str] = None) -> str:
    """
    将输入转换为有效的UUID字符串。
    - 如果value是有效的UUID，返回标准格式的UUID字符串
    - 否则返回default（必须提供有效的UUID字符串或None）
    """
    if value is None:
        return default
    try:
        uuid_obj = uuid.UUID(str(value))
        return str(uuid_obj)
    except (ValueError, AttributeError):
        return default


def estimate_tokens(text: str) -> int:
    """
    估算文本 Token 数
    规则：
    - 汉字（Unicode范围 \u4e00-\u9fa5）：1.5 token
    - 其他字符：0.3 token (英文/数字/标点等)
    """
    if not text:
        return 0

    token_count = 0.0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            token_count += 1.5
        else:
            token_count += 0.3

    return int(token_count) if token_count > 0 else 0


def save_audit_result(task_id: str, paper_id: str, agent_name: str, agent_version: str,
                      score: int, audit_level: str, result_json: dict, latency_ms: int,
                      usage_tokens: int = 0, chunk_id: Optional[str] = None, error_msg: Optional[str] = None):
    """
    将审计结果插入 agent_audits 表
    """
    try:
        conn = psycopg2.connect(**get_db_config(), cursor_factory=RealDictCursor)
        cur = conn.cursor()
        random_id = random.getrandbits(63)
        cur.execute("""
            INSERT INTO agent_audits (
                id, task_id, paper_id, chunk_id, agent_name, agent_version, status,
                score, audit_level, result_json, error_msg, usage_tokens, latency_ms,
                created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            random_id, task_id, paper_id, chunk_id, agent_name, agent_version, 'SUCCESS',
            score, audit_level, json.dumps(result_json, ensure_ascii=False), error_msg, usage_tokens, latency_ms
        ))
        conn.commit()
        cur.close()
        conn.close()
        print(f"审计结果已保存到 agent_audits，task_id: {task_id}, 手动生成 id: {random_id}")
    except Exception as e:
        print(f"保存审计结果失败: {e}")


# ---------- API 端点 ----------
@app.post("/audit/paper")
async def audit_paper(request: Dict[str, Any]):
    start = time.time()
    try:
        issues = auditor.audit_paper(request)
        details = [Detail(**iss) for iss in issues]

        total_tokens = 0
        nodes = request.get("nodes", [])
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict):
                    total_tokens += estimate_tokens(node.get("content", ""))

        base_score = 100
        audit_level = "Pass"

        if any(d.issue_type == "Contradictory_Claim" for d in details):
            base_score = 60
            audit_level = "Critical"
        elif any(d.issue_type == "Circular_Reasoning" for d in details):
            base_score = 70
            audit_level = "Warning"
        elif any(d.issue_type == "Logic_Leap" for d in details):
            base_score = 75
            audit_level = "Warning"
        elif any(d.issue_type == "Unsupported_Arg" for d in details):
            base_score = 80
            audit_level = "Warning"

        result = Result(
            score=base_score,
            audit_level=audit_level,
            comment=f"发现 {len(details)} 处逻辑问题" if details else "未发现逻辑问题",
            suggestion="请根据具体问题修改" if details else "无需修改",
            tags=list(set(d.issue_type for d in details)),
            details=details
        )
        latency = int((time.time() - start) * 1000)

        response = AuditResponse(
            request_id="paper_audit",
            agent_info=AgentInfo(name="DeepLogicAuditor", version="1.0.0"),
            result=result,
            usage=Usage(tokens=total_tokens, latency_ms=latency)
        )

        metadata = request.get("metadata", {}) if isinstance(request, dict) else {}
        task_id = safe_uuid(metadata.get("task_id"), default=str(uuid.uuid4()))
        paper_id = safe_uuid(metadata.get("paper_id"), default="00000000-0000-0000-0000-000000000000")
        chunk_id = metadata.get("chunk_id")

        save_audit_result(
            task_id=task_id,
            paper_id=paper_id,
            agent_name="逻辑审计组",
            agent_version="1.0.0",
            score=result.score,
            audit_level=result.audit_level,
            result_json=response.model_dump(),
            latency_ms=latency,
            usage_tokens=total_tokens,
            chunk_id=chunk_id,
            error_msg=None
        )

        output_file = get_output_dir() / f"audit_result_{task_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response.model_dump(), f, ensure_ascii=False, indent=2)
        print(f"审计结果已保存到: {output_file}")

        return response
    except Exception as e:
        return {"error": str(e)}


@app.post("/audit/logic")
async def audit_logic(request: AuditRequest):
    start = time.time()
    try:
        issues = auditor.audit_chunk(
            abstract=request.payload.abstract,
            content=request.payload.content,
            context_before=request.payload.context_before,
            chunk_id=request.metadata.get("chunk_id", "unknown")
        )
        details = [Detail(**iss) for iss in issues]

        total_tokens = 0
        total_tokens += estimate_tokens(request.payload.content)
        total_tokens += estimate_tokens(request.payload.abstract)
        total_tokens += estimate_tokens(request.payload.context_before)
        total_tokens += estimate_tokens(request.payload.context_after)

        base_score = 100
        audit_level = "Pass"

        if any(d.issue_type == "Contradictory_Claim" for d in details):
            base_score = 60
            audit_level = "Critical"
        elif any(d.issue_type == "Circular_Reasoning" for d in details):
            base_score = 70
            audit_level = "Warning"
        elif any(d.issue_type == "Logic_Leap" for d in details):
            base_score = 75
            audit_level = "Warning"
        elif any(d.issue_type == "Unsupported_Arg" for d in details):
            base_score = 80
            audit_level = "Warning"

        result = Result(
            score=base_score,
            audit_level=audit_level,
            comment=f"发现 {len(details)} 处逻辑问题" if details else "未发现逻辑问题",
            suggestion="请根据具体问题修改" if details else "无需修改",
            tags=list(set(d.issue_type for d in details)),
            details=details
        )
        latency = int((time.time() - start) * 1000)
        response = AuditResponse(
            request_id=request.request_id,
            agent_info=AgentInfo(name="DeepLogicAuditor", version="1.0.0"),
            result=result,
            usage=Usage(tokens=total_tokens, latency_ms=latency)
        )

        output_file = get_output_dir() / f"audit_logic_result_{request.request_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response.model_dump(), f, ensure_ascii=False, indent=2)
        print(f"审计结果已保存到: {output_file}")

        return response
    except Exception as e:
        return {"error": str(e)}


@app.post("/audit/integrated")
async def audit_integrated(paper_id: str):
    """
    一体化审计接口：从数据库读取论文，完成语义建模，按数据库规则审计，
    输出符合新规范的 JSON，并将完整结果存入 agent_audit_result 表的 result_json 字段。
    """
    start = time.time()
    try:
        # 1. 从数据库读取论文
        print(f"从数据库读取论文 ID: {paper_id}")
        db_connector = DatabaseConnector(**get_db_config())
        db_connector.connect()
        paper_data = db_connector.get_paper_by_id(paper_id)
        db_connector.close()

        if not paper_data:
            return {"error": f"论文 ID {paper_id} 不存在"}

        paper_title = paper_data.get("title", "")
        print(f"论文标题: {paper_title}")

        # 2. 切片处理和语义建模（生成 nodes, edges）
        print("进行切片处理...")
        semantic_input = slicer.generate_semantic_modeling_input_from_content(
            paper_data["content"],
            paper_id=paper_id,
            paper_title=paper_title,
        )

        all_propositions = []
        all_propositions.extend(semantic_input["abstract"]["propositions"])
        for chunk in semantic_input["chunks"]:
            all_propositions.extend(chunk["propositions"])

        print(f"总命题数量: {len(all_propositions)}")

        print("计算语义关系...")
        relations = semantic_modeler.identify_semantic_relations(all_propositions, context_window=20)
        graph = semantic_modeler.build_semantic_graph(all_propositions, relations)
        edges = [
            {"source": u, "target": v, "relation": data["relation_type"], "confidence": data["confidence"]}
            for u, v, data in graph.edges(data=True)
        ]
        if not edges and len(all_propositions) > 1:
            edges = []
            for i in range(len(all_propositions) - 1):
                edges.append({
                    "source": all_propositions[i]["prop_id"],
                    "target": all_propositions[i+1]["prop_id"],
                    "relation": "entailment",
                    "confidence": 0.7
                })

        print("构建节点列表...")
        nodes = []
        for prop in all_propositions:
            position = prop.get("position", "unknown")
            content = prop.get("content", "")
            section = "unknown"
            if position.startswith("abstract"):
                section = "summary"
            elif position.startswith("chunk"):
                section = "experiment"
                if "总结" in content or "展望" in content or "第七章" in content:
                    section = "conclusion"
            nodes.append({
                "id": prop["prop_id"],
                "content": content,
                "type": prop["type"],
                "position": position,
                "section": section
            })

        print(f"生成的节点数: {len(nodes)}, 边数: {len(edges)}")

        # 3. 从数据库获取规则
        rules = get_rules_from_db('LOG')
        print(f"从数据库获取到 {len(rules)} 条规则")

        # ---------- 4. 定义检查函数（均返回五元组：score, actual_value, suggestion, evidence, location）----------
        def check_abstract_five_part(nodes):
            """LOG-001：摘要五段式结构完整"""
            abstract_nodes = [n for n in nodes if n.get('section') == 'summary']
            if not abstract_nodes:
                return 0, "无摘要", "未找到摘要内容", "", {"section": "abstract", "line_start": 0}

            # 提取摘要文本
            abstract_text = ' '.join([n['content'] for n in abstract_nodes])

            part_keywords = {
                'background': ['背景', '研究问题', '挑战', '需求', '现状', '现有'],
                'method': ['方法', '提出', '设计', '采用', '构建', '使用'],
                'experiment': ['实验', '验证', '测试', '数据集', '对比', '评估'],
                'result': ['结果', '达到', '提升', '表明', '显示', '取得'],
                'conclusion': ['结论', '总结', '展望', '意义', '贡献']
            }

            parts_found = 0
            for part, keywords in part_keywords.items():
                if any(kw in abstract_text for kw in keywords):
                    parts_found += 1

            score = parts_found
            actual_value = f"{parts_found}/5 部分"
            suggestion = "摘要应包含背景、方法、实验、结果、结论五段" if parts_found < 5 else "摘要结构完整"

            # 证据：从摘要节点中取第一句作为示例
            evidence = abstract_nodes[0]['content'][:200] if abstract_nodes else ""
            location = {"section": "abstract", "line_start": 1}
            return score, actual_value, suggestion, evidence, location

        def check_three_level_logic(nodes):
            """LOG-002：三级逻辑闭环"""
            # 原有实现返回 (score, actual_value, suggestion)
            # 现在需要补充证据和位置
            macro_content = []
            meso_content = []
            micro_content = []
            for node in nodes:
                content = node['content'].lower()
                if any(kw in content for kw in ['理论', '框架', '模型', '体系', '架构']):
                    macro_content.append(node['content'])
                if any(kw in content for kw in ['方法', '算法', '策略', '流程', '设计']):
                    meso_content.append(node['content'])
                if any(kw in content for kw in ['实验', '测试', '验证', '仿真', '应用']):
                    micro_content.append(node['content'])

            macro_exists = len(macro_content) > 0
            meso_exists = len(meso_content) > 0
            micro_exists = len(micro_content) > 0

            score = (2 if macro_exists else 0) + (2 if meso_exists else 0) + (2 if micro_exists else 0)
            actual_value = f"宏观:{'✓' if macro_exists else '✗'}, 中观:{'✓' if meso_exists else '✗'}, 微观:{'✓' if micro_exists else '✗'}"
            suggestion = "论文形成了完整的三级逻辑闭环" if score == 6 else "论文缺少部分逻辑层级，请确保包含宏观理论、中观方法和微观实践三个层面的内容"

            # 证据：取第一句相关文本
            evidence = (macro_content[0] if macro_content else "") + (meso_content[0] if meso_content else "")
            evidence = evidence[:200]
            location = {"section": "unknown", "line_start": 0}
            return score, actual_value, suggestion, evidence, location

        def check_term_consistency(nodes):
            """LOG-004：术语一致性"""
            # 原有实现返回 (score, actual_value, suggestion)
            # 这里简化，直接返回原结果 + 默认证据
            from collections import defaultdict
            term_usage = defaultdict(lambda: defaultdict(int))
            for node in nodes:
                content = node['content']
                section = node.get('section', 'unknown')
                # 提取英文术语和中文术语（简单规则）
                terms = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]*)*|[A-Z]{2,}|\w+_(?:\w+_?)+', content)
                chinese_terms = re.findall(r'[\u4e00-\u9fff]{2,}', content)
                for term in terms + chinese_terms:
                    if len(term) > 2:
                        term_usage[term][section] += 1
            total_terms = len(term_usage)
            if total_terms == 0:
                return 4, "无术语", "未检测到术语使用", "", {"section": "unknown", "line_start": 0}
            consistent_terms = sum(1 for secs in term_usage.values() if len(secs) > 1)
            ratio = consistent_terms / total_terms
            if ratio >= 0.8:
                score = 4
            elif ratio >= 0.6:
                score = 3
            elif ratio >= 0.4:
                score = 2
            else:
                score = 1
            actual_value = f"术语一致性: {ratio:.1%} ({consistent_terms}/{total_terms})"
            suggestion = f"术语在各章节中使用较为一致" if ratio >= 0.6 else f"建议统一术语使用，目前仅{ratio:.1%}的术语在多章节中一致使用"
            evidence = "术语使用示例：" + list(term_usage.keys())[0] if term_usage else ""
            location = {"section": "unknown", "line_start": 0}
            return score, actual_value, suggestion, evidence, location

        def check_related_tech_rate(nodes):
            """LOG-005：相关技术章节闭环衔接"""
            # 原有实现返回 (score, actual_value, suggestion)
            tech_keywords = ['相关技术', '相关工作', '文献综述', '研究现状']
            transition_words = ['因此', '所以', '因而', '从而', '导致', '造成', '使得', '由此可见', '综上所述', '基于此', '于是']

            tech_start = -1
            for i, node in enumerate(nodes):
                if any(kw in node['content'] for kw in tech_keywords):
                    tech_start = i
                    break
            if tech_start == -1:
                return 0, "无相关技术章节", "未找到相关技术章节", "", {"section": "unknown", "line_start": 0}

            tech_end = -1
            for i in range(tech_start+1, len(nodes)):
                content = nodes[i]['content'].strip()
                if content and (content[0].isdigit() or '章' in content[:10] or '节' in content[:10]):
                    tech_end = i
                    break
            if tech_end == -1:
                tech_end = len(nodes)

            tech_node_count = tech_end - tech_start
            total_node_count = len(nodes)
            tech_ratio = tech_node_count / total_node_count if total_node_count > 0 else 0

            transition_count = 0
            for i in range(tech_start, tech_end):
                for word in transition_words:
                    if word in nodes[i]['content']:
                        transition_count += 1
                        break

            ratio_score = 1 if tech_ratio <= 0.2 else 0
            transition_score = min(2, transition_count)
            score = ratio_score + transition_score
            actual_value = f"占比{tech_ratio:.1%}，衔接词{transition_count}个"
            suggestion = "相关技术章节占比和衔接语良好" if score >= 2 else "建议控制相关技术章节篇幅不超过20%，并增加衔接语"
            evidence = nodes[tech_start]['content'][:200] if tech_start != -1 else ""
            location = {"section": "相关技术", "line_start": 1}
            return score, actual_value, suggestion, evidence, location

        def check_experiment_answer_question(nodes):
            """LOG-006：实验回应研究问题"""
            # 原有实现返回 (score, actual_value, suggestion)
            research_points = []
            experiment_content = []
            for node in nodes:
                content = node['content']
                section = node.get('section', 'unknown')
                if section in ['summary']:
                    # 提取问题句或目标句
                    questions = re.findall(r'[^。！？]*(?:如何|什么|为什么|怎样|解决.*问题|实现.*功能)[^。！？]*[？\?]', content)
                    research_points.extend(questions)
                    goals = re.findall(r'(?:旨在|为了|目标是|目的是|解决|实现|提出).*?(?:[。！？]|\.)', content)
                    research_points.extend(goals)
                if '实验' in content or '验证' in content or '测试' in content or section == 'experiment':
                    experiment_content.append(content)
            if not research_points:
                research_points = ["研究问题（未明确提取）"]
            experiment_text = ' '.join(experiment_content)
            match_count = 0
            for point in research_points:
                point_keywords = re.findall(r'[\w\u4e00-\u9fff]{3,}', point)
                if any(kw in experiment_text for kw in point_keywords):
                    match_count += 1
            total = len(research_points)
            ratio = match_count / total if total > 0 else 0
            if ratio >= 0.8:
                score = 3
            elif ratio >= 0.5:
                score = 2
            else:
                score = 1
            actual_value = f"实验回应率: {ratio:.1%} ({match_count}/{total})"
            suggestion = "实验有效回应了研究问题" if ratio >= 0.6 else "实验对研究问题的回应不足，建议加强实验设计"
            evidence = experiment_content[0][:200] if experiment_content else ""
            location = {"section": "实验部分", "line_start": 1}
            return score, actual_value, suggestion, evidence, location

        def check_innovation_count(nodes):
            """LOG-007：创新点数量达标"""
            conclusion_nodes = [n for n in nodes if n.get('section') == 'conclusion']
            if not conclusion_nodes:
                return 0, "无结论章节", "未找到结论章节", "", {"section": "conclusion", "line_start": 0}
            conclusion_text = ' '.join([n['content'] for n in conclusion_nodes])
            sentences = re.split(r'[。！？]', conclusion_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            keywords = ['创新', '首次', '提出', '贡献', '主要工作']
            innovation_sentences = set()
            for sent in sentences:
                if any(kw in sent for kw in keywords):
                    innovation_sentences.add(sent)
            count = len(innovation_sentences)
            if count >= 3:
                score = 4
                suggestion = "结论中创新点明确"
            elif count == 2:
                score = 3
                suggestion = "创新点较明确，建议再增加1个"
            elif count == 1:
                score = 2
                suggestion = "结论中创新点较少，建议补充"
            else:
                score = 0
                suggestion = "结论中未发现明显创新点"
            actual_value = f"{count}个创新句"
            evidence = list(innovation_sentences)[0][:200] if innovation_sentences else ""
            location = {"section": "conclusion", "line_start": 1}
            return score, actual_value, suggestion, evidence, location

        # 5. 规则映射
        rule_check_map = {
            'LOG-001': check_abstract_five_part,
            'LOG-002': check_three_level_logic,
            'LOG-004': check_term_consistency,
            'LOG-005': check_related_tech_rate,
            'LOG-006': check_experiment_answer_question,
            'LOG-007': check_innovation_count,
        }

        # 6. 执行检查并收集结果
        audit_results = []
        inserted_count = 0
        for rule in rules:
            rule_id = rule['rule_id']
            full_score = rule['full_score']

            if rule_id not in rule_check_map:
                print(f"警告: 未实现规则 {rule_id} 的检查函数")
                continue

            check_func = rule_check_map[rule_id]
            score_obtained, actual_value, suggestion, evidence, location = check_func(nodes)

            # 生成 result_id
            result_id = str(uuid.uuid4()).replace('-', '')[:32]

            # 构建审计项
            audit_item = {
                "result_id": result_id,
                "paper_id": paper_id,
                "point": rule['rule_name_cn'],
                "rule_id": rule_id,
                "score": score_obtained,
                "level": rule['severity'],
                "description": suggestion if score_obtained < full_score else "符合规范",
                "evidence_quote": evidence,
                "location": location,
                "suggestion": suggestion
            }
            audit_results.append(audit_item)

            # 插入数据库（包括 result_json 字段）
            conn = None
            try:
                conn = psycopg2.connect(**get_db_config())
                cur = conn.cursor()
                paper_id_clean = paper_id.replace('-', '')
                cur.execute("""
                    INSERT INTO agent_audit_result (
                        result_id, paper_id, paper_name, agent_code, rule_id,
                        is_compliant, actual_value, score_obtained, audit_suggestion, audit_time, result_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                """, (
                    result_id,
                    paper_id_clean,
                    paper_title,
                    'LOG',
                    rule_id,
                    1 if score_obtained == full_score else 0,
                    str(actual_value),
                    score_obtained,
                    suggestion,
                    json.dumps(audit_item, ensure_ascii=False)  # 存入单个审计项的 JSON
                ))
                conn.commit()
                inserted_count += 1
                print(f"规则 {rule_id} 审计结果已插入，得分 {score_obtained}/{full_score}")
            except Exception as e:
                print(f"插入规则 {rule_id} 失败: {e}")
                if conn:
                    conn.rollback()
            finally:
                if conn:
                    conn.close()

        # 7. 准备响应体（符合新格式）
        response_body = {
            "agent_code": "LOG",
            "audit_results": audit_results
        }

        # 8. 保存结果到文件（可选）
        task_id = str(uuid.uuid4())
        output_file = get_output_dir() / f"audit_result_{task_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response_body, f, ensure_ascii=False, indent=2)
        print(f"审计结果已保存到: {output_file}")
        print(f"成功插入 {inserted_count}/{len(rules)} 条规则到 agent_audit_result")

        latency = int((time.time() - start) * 1000)
        print(f"一体化审计完成，耗时: {latency}ms")
        return response_body

    except Exception as e:
        print(f"一体化审计失败: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}