## topics
A Survey on Deep Reinforcement Learning for Data Processing and Analytics
Security Risk and Attacks in AI: A Survey of Security and Privacy
Graph Retrieval-Augmented Generation for Large Language Models: A Survey
A Survey on Machine Learning Approaches and Its Techniques
A Survey on Edge Computing Systems and Tools

## commands to generate lists

curl -X POST http://localhost:3001/api/query \
  -H "Content-Type: application/json" \
  -d '{"topic":"Deep Reinforcement Learning for Data Processing and Analytics","max_results":30}'


curl -X POST http://localhost:3001/api/query \
  -H "Content-Type: application/json" \
  -d '{"topic":"Security Risk and Attacks in AI","max_results":30}'


curl -X POST http://localhost:3001/api/query \
  -H "Content-Type: application/json" \
  -d '{"topic":"Graph Retrieval-Augmented Generation for Large Language Models","max_results":30}'




curl -X POST http://localhost:3001/api/query \
  -H "Content-Type: application/json" \
  -d '{"topic":"Machine Learning Approaches and Its Technique","max_results":30}'




curl -X POST http://localhost:3001/api/query \
  -H "Content-Type: application/json" \
  -d '{"topic":"Edge Computing Systems and Tools","max_results":30}'

## commands to run eval_query.py
assume in eval_query dir
python3 eval_query.py ./goldlists/deepRL_cites.txt ../../app/data/query_pipe_out_deep_reinforcement_learning_for_data_processing_and_analytics_20251116_210126.json

python3 eval_query.py ./goldlists/edge_computing_cites.txt ../../app/data/query_pipe_out_edge_computing_systems_and_tools_20251116_210618.json

python3 eval_query.py ./goldlists/graphRAG_LLM_cites.txt ../../app/data/query_pipe_out_graph_retrieval_augmented_generation_for_large_language_models_20251116_210448.json

python3 eval_query.py ./goldlists/ML_cites.txt ../../app/data/query_pipe_out_machine_learning_approaches_and_its_technique_20251116_210527.json

python3 eval_query.py ./goldlists/securityriskandattacks_cites.txt ../../app/data/query_pipe_out_edge_computing_systems_and_tools_20251116_210618.json




