# gaokao-ai-rate-template

把 `data/all.json` 和 `data/data.json` 放进仓库后，GitHub Actions 会自动执行：

1. 规范化专业数据
2. 规范化岗位数据
3. 计算专业 AI 当前替代风险指数
4. 输出到 `output/major_ai_rate.json`

## 使用方法

- 把高考专业数据放到 `data/all.json`
- 把招聘数据放到 `data/data.json`
- 根据你的专业代码维护 `config/major_job_rules.json`
- 根据你的口径维护 `config/ai_replace_rules.json`
- push 到 `main` 或手动运行 workflow

## 输出文件

- `output/majors.normalized.json`
- `output/jobs.normalized.json`
- `output/major_ai_rate.json`
- `output/major_ai_rate.debug.json`

## 可选升级

- 增加专业类批量映射
- 增加 TF-IDF / embedding 相似度
- 增加历史版本 diff
- 自动发布到 GitHub Pages
