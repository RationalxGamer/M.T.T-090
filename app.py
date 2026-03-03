import streamlit as st
from exa_py import Exa
from groq import Groq

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
                
                search_results = exa.search_and_contents(
                    search_query,
                    type="neural",
                    use_autoprompt=True,
                    num_results=3, # Pulls the top 3 best transcriptions
                    text=True
                )
                
                # Combine the raw text from the websites
                context_text = ""
                for result in search_results.results:
                    context_text += f"Content: {result.text}\n\n"
                    
                # --- B. The Brain Phase (Groq) ---
                prompt = f"""
                You are an expert bilingual music theory assistant. Based ONLY on the following forum text, extract the musical data for the song '{song_input}'.
                
                Please provide:
                1. **Key:** 2. **Tempo (BPM):** 3. **Chord Progression:** Create a clean, measure-by-measure Markdown table of the chords.
                
                Raw Data to analyze:
                {context_text}
                """
                
                chat_completion = groq.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-8b-8192", # Groq's blazing fast model
                    temperature=0.2, # Keeps the AI focused and accurate
                )
                
                # --- C. Display the Result ---
                st.success("Analysis Complete!")
                st.markdown(chat_completion.choices[0].message.content)

            except Exception as e:
                st.error(f"Looks like we hit a snag: {e}")
    else:
        st.warning("Please type a song name first!")