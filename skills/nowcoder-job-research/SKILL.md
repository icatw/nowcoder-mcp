---
name: nowcoder-job-research
description: Use the nowcoder MCP tools to research 牛客面经, 求职进度, 内推, 公司评价, and interview prep.
---

# Nowcoder Job Research

Use when the user asks for 牛客, Nowcoder, 面经, 求职进度, 内推, 公司评价, or company/role interview preparation.

## Workflow

1. Build several focused queries:
   - `{company} {role} 面经`
   - `{company} {tech_stack} 面经`
   - `{company} 求职进度`
   - `{company} OC 泡池 感谢信`
2. Prefer `search_nowcoder_interviews` for a single company/role target.
3. Use `search_nowcoder` with `tag="interview"` for 面经, `tag="progress"` for 求职进度, `tag="referral"` for 内推, and `tag="company_review"` for 公司评价.
4. Fetch details for high-signal results using `get_nowcoder_discuss_detail` or `get_nowcoder_feed_detail` based on `rc_type`.
5. Summarize with source URLs and dates when available.

## Output Guidance

For interview prep, group by:

- 高频技术题
- 项目深挖点
- 算法/系统设计
- 岗位/部门信号
- 求职流程与时间线
- 学习路线和模拟面试题

## Safety

- Treat posts as anecdotal and possibly outdated.
- Label uncertainty.
- Do not ask for or expose cookies.
- Do not perform write operations on Nowcoder.
