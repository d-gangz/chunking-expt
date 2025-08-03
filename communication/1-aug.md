Here is my reply update to the team:

Note that I am Gang. Jair is the Machine Learning Engineer, Mark is the Product Manager, while Jake is the Backend Engineer.

# Convo 1

<Gang's update>
Hey team, here’s an update on the chunking experiment progress.
:white_check_mark: What’s Been Completed Since Last Update
Base Ground Truth Dataset Creation
Generated 30 comprehensive insights with 90 questions using a systematic LLM approach
Process:
Fed all 5 transcripts to GPT-4.1 with instructions to extract cross-transcript insights
Each insight includes 2-4 verbatim quotes (50-150 words) from the source transcripts
Generated 2-3 questions per insight with varying difficulty levels (easy/medium/hard
Prioritized insights that connect concepts across multiple transcripts
Validated all quotes exist verbatim in the original transcripts
Attaching base_ground_truth.json with examples
Fixed-Size Chunks Evaluation
Completed first evaluation using Phoenix (open-source eval framework, maintaining data security)
MRR@10: 0.49 - Mean Reciprocal Rank measures where the first relevant result appears (0.49 ≈ first relevant result typically at position 2)
Recall@10: 0.54 - We’re finding 54% of relevant chunks in top 10 results
Precision@10: 0.19 - Among top 10 results, 19% are relevant
(attached image shows the result for using search results @10,20,30. The 1st row is results where I use retrieved search results=30)
Why Recall Matters Most (compared to the other 2): Since our RAG system synthesizes answers rather than showing search results, recall is critical - we need to capture relevant information even if it means retrieving more chunks. The 54% recall suggests room for improvement in our retrieval strategy.
:arrows_counterclockwise: Evaluation Approach
The Challenge: Different chunking strategies create different boundaries, making direct comparison difficult.
Solution:
Create one base ground truth dataset (see attached base_ground_truth.json) with questions and comprehensive answers backed by exact quotes
For each chunking strategy, automatically map these quotes to the relevant chunks using 80%+ text overlap. see phoenix_dataset_simplified_v2.json For a sample of the derived labelled dataset for the fixed chunk strategy.
This creates chunking-specific labeled datasets from the same base, ensuring fair comparison
Key Question: Do you agree with this approach of creating one base ground truth dataset and mapping it to each chunking strategy? This avoids manually labeling datasets for each chunking method while ensuring consistent evaluation.
:dart: Key Alignment Needed
Base Ground Truth Dataset Review: The attached base_ground_truth.json contains questions that simulate what members might search for
Critical: We need team alignment on this dataset as it drives all evaluations
please review the attached examples for:
Question relevance to member needs
Coverage of key topics
Difficulty distribution
Transcript Scope
Currently using 5 legal/business transcripts for the base dataset
Question: Is this scope appropriate, or should we adjust?
:rocket: My Next Steps
Research nuggetization as the next chunking strategy to evaluate
Refine base ground truth dataset based on team feedback
Run evaluations for other chunking methods
:speech_balloon: Questions for the Team
Do you agree with using one base ground truth dataset that we map to each chunking strategy for evaluation?
Is the 5-transcript scope appropriate for creating this base dataset?
Should we search against just these 5 transcripts or search against the entire transcript database? (entire transcript database would be best but I’m unsure the effort and probably need Jake’s help on it)
The base ground truth dataset is the foundation for fair comparison. So your input on the attached examples is crucial for ensuring we’re testing against realistic member queries :relaxed:.
Here’s the github project if you want to dig deeper.
Looking forward to hearing your thoughts! (edited)
</Gang's Update>

<Jair's reply>
Great work @Gang!
it was hard to setup phoenix?
Do you agree with using one base ground truth dataset that we map to each chunking strategy for evaluation?
I think that make sense, but regarding if the questions are meaningful I think that we should ask Kiran or Greg
Is the 5-transcript scope appropriate for creating this base dataset?
I think so, we can considere this as our "training" dataset and to ensure that winning strategy is indeed good we can test in the whole database
Should we search against just these 5 transcripts or search against the entire transcript database? (entire transcript database would be best but I’m unsure the effort and probably need Jake’s help on it)
yeah, I think that the entire database would be better
</Jair's reply>

<My reply>
Phoenix setup was not too difficult. It is pretty good as:
Open-source
Has a wide range of integration including Haystack (I think its the LLM framework the team is using?)
Can be run locally even in a project folder
Hmm just that the docs is a bit hard to decipher when I wana do something a bit more custom. Like I was trying to figure how to filter the experiment results by the metadata defined (I’ve set it up in the dataset) but I can’t really find it in the docs nor AI searches :((
-------
For the questions:
Got it!
:+1:
Got it. I’ll coordinate with Jake on it.
</My reply>

# Convo 2

<Gang's message>
Collaboration Opportunity with Jake
Great to have Jake joining the effort! As he mentioned, he’s able help.
Areas where Jake’s help would be valuable (Jake, let me know if these align with your thoughts):
Database Setup: Since you have access to the production database with full transcript metadata, would you be able to help set up test databases for different chunking strategies? I’ll update u on the different chunking strategies.
Search Endpoints: Could you provide curl commands or API endpoints for hybrid search once the databases are ready? This would help with the Evals (I’ll provide more details on the hybrid search req. for the search too).
Production Insights: Your experience with the actual codebase could help ensure our experiments align with production constraints.
@Jake Cillay would this collaboration approach work for you? Happy to adjust based on what makes most sense!
@Mark @Jair Neto feel free to suggest what would work best too. (edited)
</Gang's message>

<Jake's reply>
This sounds good to me @Gang !!
I would be happy to set this up to start working with production ready transcripts - may need to work with Devops through it.
I’m not sure if we can provide external endpoints for internal functions with out current infrastructure - but can work on investigating that.
since Lloyd isn’t released to users yet I don’t think it will effect any other tool within production. We can set up pipelines and config variables to help ease into and test different chunking strategies in prod though!
Happy to talk further and start working out a schedule if @Jair Neto and @Mark think it’s a good route to begin on!!
</Jake's reply>
