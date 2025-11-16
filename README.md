# QuickLit

## run project with docker
- prereq:
create `/backend/app/.env` to store opanai API key: `OPENAI_API_KEY=your_key_no_quotes` and `SMITHERY_API_KEY=your_key_no_quotes`

- verify individual service runs
`docker build -t quicklit-frontend ./quicklit-web`
`docker build -t quicklit-frontend ./quicklit-web`

- start all services
`docker compose up --build -d`

- stop & remove all
`docker compose down`

- access frontend:localhost:8080 
& backend: `curl http://localhost:3001`, expect: {"detail":"Not Found"}


## Backend APIs
### @app.post("/api/query")
- uses query_pipe.py (better retrival quality than query_mcp.py, query_single_prompt.py)
- also log all intermidate results including final list of paper to backend/app/data/query_pipe_{topic}_{timestamp}.json
- input param: topic, max_results
- expected output: 
```
{
  "papers": [
    {
      "title": "<string>",
      "pdf_url": "<string>",
      "paper_id": "<string>"
    }
  ]
}
```
- to test: open terminal inside backend container `docker exec -it backend bash`,  edit if__main__ section of query_pipe.py for arbitrary topic & max_count, then run with `python3 query_pipe.py`
> 
```
curl -X POST http://localhost:3001/api/query \
  -H "Content-Type: application/json" \
  -d '{"topic":"Human-AI collaboration models for improving decision accuracy in complex analytical workflows","max_results":5}'

```
```
{"papers":[{"title":"Learning to Complement and to Defer to Multiple Users","pdf_url":"https://arxiv.org/pdf/2407.07003.pdf","paper_id":"2407.07003"},{"title":"Cost-Sensitive Learning to Defer to Multiple Experts with Workload Constraints","pdf_url":"https://arxiv.org/pdf/2403.06906.pdf","paper_id":"2403.06906"},{"title":"Coverage-Constrained Human-AI Cooperation with Multiple Experts","pdf_url":"https://arxiv.org/pdf/2411.11976.pdf","paper_id":"2411.11976"},{"title":"DeCoDe: Defer-and-Complement Decision-Making via Decoupled Concept Bottleneck Models","pdf_url":"https://arxiv.org/pdf/2505.19220.pdf","paper_id":"2505.19220"},{"title":"A2C: A Modular Multi-stage Collaborative Decision Framework for Human-AI Teams","pdf_url":"https://arxiv.org/pdf/2401.14432.pdf","paper_id":"2401.14432"}]}%  
```

### @app.get("/api/get_summary")
- input param: pdf_url
- sample output:
```
{
  "summary": "This paper proposes a cooperative human-AI decision-making workflow...",
  "type": "summary",
  "cached": false
}
```
#### I/O eg1: paper too long, instead of summarize full text, just return abstract
```
curl "http://localhost:3001/api/get_summary?url=https://arxiv.org/pdf/1911.02794"
```

```
{"summary":"Driven by the visions of Internet of Things and 5G communications, the edge computing systems integrate computing, storage and network resources at the edge of the network to provide computing infrastructure, enabling developers to quickly develop and deploy edge applications. Nowadays the edge computing systems have received widespread attention in both industry and academia. To explore new research opportunities and assist users in selecting suitable edge computing systems for specific applications, this survey paper provides a comprehensive overview of the existing edge computing systems and introduces representative projects. A comparison of open source tools is presented according to their applicability. Finally, we highlight energy efficiency and deep learning optimization of edge computing systems. Open issues for analyzing and designing an edge computing system are also studied in this survey.","type":"abstract","timeout":false,"warning":"File too long (3205.5 KB > 976.6 KB), showing abstract only.","cached":false}%  
```
### I/O eg2: have request summary before, return cached
```
curl "http://localhost:3001/api/get_summary?url=https://arxiv.org/pdf/2407.12345.pdf"
```
```
{"summary":"### Summary of \"VisionTrap: Vision-Augmented Trajectory Prediction Guided by Textual Descriptions\"\n\n#### Introduction\nThe paper introduces VisionTrap, a method for trajectory prediction of road agents in autonomous driving environments. Traditional models mainly use past trajectories and HD maps, excluding rich contextual information available from visual inputs such as human behaviors and gestures. VisionTrap enhances trajectory prediction by incorporating visual semantics from surround-view cameras and textual descriptions generated using a Vision-Language Model (VLM).\n\n---\n\n#### Methods\n1. **Architecture**: VisionTrap consists of several modules:\n   - **Per-Agent State Encoder**: Encodes agent-specific observations (past trajectories, types) into embeddings.\n   - **Visual Semantic Encoder**: Integrates visual data into a Bird’s Eye View (BEV) feature, leveraging multi-view images.\n   - **Text-Driven Guidance**: Uses textual descriptions derived from visual inputs to guide and refine trajectory predictions.\n   - **Trajectory Decoder**: Predicts future poses of agents based on the augmented state embeddings.\n\n2. **Visual Integration**: Visual data is encoded into a BEV feature to enhance understanding of the driving scene. The model employs deformable attention mechanisms to focus on relevant information areas for each agent.\n\n3. **Textual Guidance**: The model uses a contrastive loss function to align textual descriptions with visual features, refining the learning process to incorporate richer contextual understanding.\n\n4. **Objective**: The overarching goal of the method is to enhance real-time trajectory prediction accuracy while maintaining low latency (53 ms) suitable for autonomous driving.\n\n---\n\n#### Datasets\n- **nuScenes-Text Dataset**: The authors created this dataset by augmenting the existing nuScenes dataset with textual annotations. An automated process involving a VLM and a Large Language Model (LLM) was utilized to generate and refine textual descriptions related to agent behaviors and environmental contexts.\n\n---\n\n#### Metrics\nThe performance evaluation relies on standard metrics relevant to trajectory prediction, specifically:\n- **Average Displacement Error (ADE)**\n- **Final Displacement Error (FDE)**\n- **Miss Rate (MR)**\n\nThese metrics are used to quantify the accuracy of predictions against ground truth data.\n\n---\n\n#### Findings\n1. **Performance Enhancements**: VisionTrap demonstrated a significant improvement (27.56% reduction in FDE) compared to existing models. The real-time aspect of prediction is a strong advantage, outpacing prior methods with similar accuracy levels.\n   \n2. **Qualitative Results**: Qualitative analyses indicate that the model effectively utilizes visual and textual inputs to enhance trajectory predictions, showcasing improved behavior understanding in various urban driving scenarios.\n\n3. **Dataset Validation**: Human evaluations of the nuScenes-Text dataset revealed a high accuracy (94.8%) in image-text alignment, affirming the dataset's utility for enhancing trajectory prediction tasks.\n\n---\n\n#### Conclusion\nVisionTrap illustrates the potential of integrating visual semantics and linguistic guidance into trajectory prediction models. The proposed method effectively addresses limitations of traditional approaches and highlights the importance of employing multimodal data to improve safety and reliability in autonomous driving contexts. The release of the nuScenes-Text dataset aims to further facilitate research and development in this domain.\n\n---\n\nFor more details, the project can be accessed at [VisionTrap Project Page](https://moonseokha.github.io/VisionTrap).","type":"summary","timeout":false,"cached":true}
```