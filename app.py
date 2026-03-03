import streamlit as st
from exa_py import Exa
from groq import Groq
import re

# 1. Setup the UI
st.set_page_config(page_title="Music Breakdown Tool", page_icon="🎵")
st.title("🎵 Spanish & Universal Music Tool")
st.write("Enter a song title and artist to get the key, tempo, and measure-by-measure chords.")

# 2. Connect the Keys (Securely pulling from your Streamlit Vault)
try:
    exa = Exa(api_key=st.secrets["EXA_API_KEY"])
    groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("API keys not found. Please check your Streamlit Secrets.")
    st.stop()

# 3. The Search Bar
song_input = st.text_input("Song Title & Artist", placeholder="e.g., Vivir Mi Vida - Marc Anthony")

# 4. The "Analyze" Button Logic
if st.button("Analyze Song"):
    if song_input:
        with st.spinner(f"Scouring music forums for '{song_input}'..."):
            try:
                # --- A. The Search Phase (Exa) ---
                search_query = f"{song_input} chords key bpm measure breakdown site:lacuerda.net OR site:ultimate-guitar.com OR site:songsterr.com"
                
                # Note: use_autoprompt removed to fix the Exa API error
                search_results = exa.search_and_contents(
                    search_query,
                    type="neural",
                    num_results=3, 
                    text=True
                )
                
                # Combine the raw text from the websites
                context_text = ""
                for result in search_results.results:
                    context_text += f"Content: {result.text}\n\n"
                    
                # --- B. The Brain Phase (Groq) ---
                # Updated Strict Prompt with Accuracy Estimate
                prompt = f"""
                You are a professional Musicologist. Extract high-accuracy musical data for '{song_input}' using the provided text.
                
                STRICT RULES:
                1. DO NOT GUESS. If BPM or Key isn't found in the text, say "Unknown".
                2. FAVOR TABLATURE: Look for chord symbols (e.g., Bb, Cm7) placed over lyrics or in grids.
                3. BILINGUAL SUPPORT: If you see Spanish notes (Do, Re, Mi, Fa, Sol, La, Si), translate them to English (C, D, E, F, G, A, B).
                4. TABLE FORMAT: Provide the chord progression in a clear Markdown table by section (Intro, Verse, Chorus).
                
                ACCURACY ESTIMATE:
                At the very end of your response, provide an "Accuracy Confidence Score" from 0-100%. 
                - 90%+: Found matching data on multiple sites.
                - 50-70%: Data found but looks incomplete or formatted poorly.
                - Below 50%: Highly speculative; data was messy or missing.
                Explain in one sentence WHY you gave that score.

                TEXT TO ANALYZE:
                {context_text}
                """
                
                # Updated to Groq's latest model
                chat_completion = groq.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                    temperature=0.2, 
                )
                
                # --- C. Display the Result ---
                st.success("Analysis Complete!")
                response_content = chat_completion.choices[0].message.content
                st.markdown(response_content)

                # --- D. Accuracy Visualization ---
                # This part looks for the % number in the AI's message and makes a visual bar
                match = re.search(r"(\d+)%", response_content)
                if match:
                    score = int(match.group(1))
                    st.write(f"**Tool Confidence Score: {score}%**")
                    # Streamlit progress bars expect a float between 0.0 and 1.0
                    st.progress(score / 100.0) 

            except Exception as e:
                st.error(f"Looks like we hit a snag: {e}")
    else:
        st.warning("Please type a song name first!")