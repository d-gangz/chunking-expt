I'm going to drop an update to my client in terms of what has been done for the chunking experiment.

And here is the previous update I've given them.

<progress update>
Hey team, a progress update for the chunking work.
I’m establishing the foundation to evaluate different chunking strategies for video transcript retrieval.
:white_check_mark: What has been completed:
Database: Supabase Postgres (open source) to mirror our production Postgres setup
Ensures data privacy and security by running locally
Maintains compatibility with our existing infrastructure
Hybrid Search: Combines vector similarity and full-text search using:
OpenAI embeddings (text-embedding-3-large, 1,024 dimensions)
Utilised Hybrid search implementation from Supabase docs.
HSNW index for semantic vector search
Reciprocal Rank Fusion (RRF)
:large_yellow_circle: Current Status:
Working on dataset labeling for fixed-size chunks (simple common chunking for baseline)
Using OpenAI’s default chunking recommendations (see: https://platform.openai.com/docs/guides/retrieval#chunking):
OpenAI defaults: 800 tokens with 400-token overlap (50%). This would correspond to 3200 Characters with 1600 token overlap as OpenAI estimates 1 token to be roughly 4 characters.
My implementation: 3,000 characters with 1,500-character overlap (50%) to align with OpenAI’s ~4 characters per token approximation. I used a slightly lower value from OpenAI to account for some variance.
:ladder: Next Steps:
Complete dataset labeling and evaluation for fixed-sized chunks
Research on Nuggestisation to run the evaluation
Compare retrieval effectiveness across different chunking strategies
:link: Here’s the link to the github project for this chunking task
Lemme know if you’ve questions. Thanks! (edited) 
</progress update>

So first and foremost, at the update, then what I've completed is:

1. The dataset labeling
2. The evaluation for the fixed-size chunks which I'll attach the image there.

The next most important thing is to explain what the next steps should be with them. I think perhaps like layout, what is the entire eval pipeline first, and what are the challenges. Maybe which parts would be great for Jake to help me with. Starting from the sounding portion, the most challenging portion is actually creating the labeled dataset because if we can have a labeled dataset as close as possible to what members would usually search for, then that would be fantastic.

use 4_labelled_dataset/baseline-questions as extra context. Because the tricky part is we are testing different chunking strategies. So you can imagine for each chunking strategy, the way the data is chunked is very different. So we don't have a common baseline. In this case, how do we establish a baseline so that we can compare the different chunking strategies together? Therefore, my approach was listed in this folder that was mentioned itself because we are trying to create this ground-truth dataset that we can use to create the label datasets for the different chunking strategies, and that's the main point of doing this labeled dataset.

And it will be good for the label dataset to just focus on a few transcripts to keep the scope more constrained so that we know what we are testing. I think first is to gain alignment, is it OK? We still use this existing 5 transcripts that we are using to create the label dataset, etc. And I will also be sending them the JSON that I've created. That is the base label dataset that I will use to create the label dataset for the different chunking strategies. We also briefly explain to them how using this base label dataset we can create a label dataset for the different chunking strategies based on whatever you can see in that folder.

Based on the different stages of how the eval is done:

1. We have to transcribe the audio
2. Then we'll chunk it
3. Finally, we'll throw it in the database and create our label dataset based on the base label dataset that we have aligned on The base label dataset is something that we need to align on because we can use that to create a label dataset for the different chunk strategies. This is more like a better way of comparison and explanation to them on how we do this process of using the base labeled dataset to create a label dataset for the different chunk strategies. After that, we will conduct the evaluation which is just creating a function that does a search. Perhaps how where Jake can help me is because he has access to the database and all data, so maybe he can assist on the creation of the databases for the different chunk strategies that we are aligning on. Then from there, he can create a curl command for me to code to do the hybrid search. Based on the number of chunking strategies, each chunking strategy ideally if you have one curl command he can pass over to me so I can create it to retrieve the results and then we can do the eval.

Additional context: I'm talking to the product manager and also the machine learning engineer. I'll have another backend engineer called Jake who can potentially help me.

this is what Jake wrote
"ey Gang, how's it going? Not sure if we've met, but my name's Jake and Im an engineer for the Suite! I was planning to work on chunking for video transcripts and wanted to help you in any way I can - is there something that you might need help with right now or something you'd like me to do? I was thinking I could start transitioning the chunking strategy into our actual codebase to work with real data and set up the pipeline flows or anything else you have in mind :simple_smile: let me know!"

What I need your help with is to read through the different parts of my codebase that can help me craft a reply to my client based on all these contexts that I've shared. Like, "What is my progress?" "What is the context in terms of what I need help on?" "What are the certain positions that we need to align on?" For example.

Please keep it concise to the point so that it's skimmable for everybody to understand the progress, the next steps, and what are the things we need to be aligned on, especially on this base label dataset.
