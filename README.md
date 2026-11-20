# Latebind（晚维台）基座

事实先入未绑区 → 维度晚到回填 → 绑定入正式区 → 超龄隔离互证。

## 一键启动

```powershell
cd d:\document\cccodeLYH\initProject\latebind
docker compose up --build -d
```

- 前端：http://localhost:6100  
- API 文档：http://localhost:11100/docs  

改端口：编辑本目录 `.env` 的 `FRONTEND_PORT` / `API_PORT`。

## 跑题目录

题面独立工程放在 `workspace/latebind/latebindN/`，端口：

| 题 | 前端 | API |
| --- | --- | --- |
| latebind1 | 6100 | 11100 |
| latebind2 | 6101 | 11101 |
| latebindN | 6100+(N-1) | 11100+(N-1) |
