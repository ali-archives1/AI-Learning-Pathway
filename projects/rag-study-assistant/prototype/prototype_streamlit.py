import streamlit as st
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama


st.set_page_config(
    page_title="RAG Study Assistant",
    page_icon="📚",
)

st.title("📚 RAG Study Assistant")
st.write("Upload a PDF and ask questions using only its information.")

uploaded_file = st.file_uploader(
    "Upload your notes",
    type=["pdf"],
)

if uploaded_file is not None:
    try:
        reader = PdfReader(uploaded_file)
        documents = []

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""

            if page_text.strip():
                documents.append(
                    Document(
                        page_content=page_text,
                        metadata={
                            "page": page_number,
                            "file": uploaded_file.name,
                        },
                    )
                )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=150,
        )

        chunks = splitter.split_documents(documents)

        with st.spinner("Preparing your PDF..."):
            embedding_model = OllamaEmbeddings(
                model="nomic-embed-text:latest"
            )

            vector_store = InMemoryVectorStore(
                embedding=embedding_model
            )

            vector_store.add_documents(chunks)

        st.success(
            f"Ready! Loaded {len(reader.pages)} pages "
            f"and created {len(chunks)} chunks."
        )

        with st.form("question_form"):
            question = st.text_input(
                "Ask a question about the PDF:"
            )

            ask_button = st.form_submit_button("Ask")

        if ask_button and question.strip():
            results = vector_store.similarity_search(
                question,
                k=4,
            )

            context_sections = []

            for result in results:
                page = result.metadata.get("page", "Unknown")

                context_sections.append(
                    f"SOURCE PAGE {page}:\n"
                    f"{result.page_content}"
                )

            context = "\n\n".join(context_sections)

            prompt = f"""
You are a careful study assistant.

Answer the question using only the PDF context below.

Instructions:
1. Read every context section carefully.
2. Look for sentences that directly or indirectly answer the question.
3. If the context contains enough information, answer clearly.
4. Do not reject an answer just because the wording differs from the question.
5. Do not use outside knowledge.
6. Do not invent facts.
7. Only say "I could not find that in the provided PDF."
   when none of the context sections contain useful information.
8. Keep the answer simple and focused.
9. Mention the supporting page number.

PDF CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

            with st.spinner("Finding the answer..."):
                llm = ChatOllama(
                    model="llama3.2:3b",
                    temperature=0,
                )

                response = llm.invoke(prompt)

            st.subheader("Answer")
            st.write(response.content)

            source_pages = sorted(
                {
                    result.metadata.get("page")
                    for result in results
                    if result.metadata.get("page") is not None
                }
            )

            st.caption(
                "Retrieved pages: "
                + ", ".join(map(str, source_pages))
            )

            with st.expander("View retrieved sections"):
                for number, result in enumerate(
                    results,
                    start=1,
                ):
                    page = result.metadata.get(
                        "page",
                        "Unknown",
                    )

                    st.markdown(
                        f"### Result {number} — Page {page}"
                    )

                    st.write(result.page_content)

    except Exception as error:
        st.error(f"Error: {error}")
    