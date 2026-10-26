"""Document upload screen."""

import streamlit as st

from services.document_service import (
    DOCUMENT_CATEGORIES,
    add_document_record,
    extract_document_text,
    load_document_index,
    save_uploaded_file,
)


def show_documents():
    """Upload a fictional document, extract text, and store its category."""
    st.title("Financial Documents")
    st.write("Upload sample financial documents.")
    st.info("Use fictional or redacted documents only.")

    notice = st.session_state.pop("document_notice", None)
    if notice:
        st.success(notice)
    document_error = st.session_state.pop("document_error", None)
    if document_error:
        st.error(document_error)

    category = st.selectbox(
        "Document category",
        DOCUMENT_CATEGORIES,
        key="document_category",
    )
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "png", "jpg", "jpeg", "txt"],
        key="document_uploader",
    )

    if uploaded_file is not None:
        extension = uploaded_file.name.rsplit(".", 1)[-1].upper()
        st.write("Filename:", uploaded_file.name)
        st.write("Size:", uploaded_file.size, "bytes")
        st.write("File type:", uploaded_file.type or extension)
        st.write("Document category:", category)

        if st.button("Save and Process", key="save_and_process"):
            try:
                file_path = save_uploaded_file(uploaded_file)
                text = extract_document_text(file_path)
                add_document_record(
                    original_filename=uploaded_file.name,
                    stored_filename=file_path.name,
                    category=category,
                    size_bytes=uploaded_file.size,
                )
            except (ValueError, OSError, RuntimeError) as error:
                st.session_state.document_error = str(error)
                st.rerun()
            else:
                st.session_state.last_extraction = {
                    "stored_filename": file_path.name,
                    "original_filename": uploaded_file.name,
                    "text": text,
                }
                st.session_state.document_notice = (
                    "Document saved successfully."
                )
                st.rerun()

    last_extraction = st.session_state.get("last_extraction")
    if last_extraction:
        st.write("Stored file:", last_extraction["stored_filename"])
        text = last_extraction["text"]
        if text.strip():
            st.subheader("Extracted Text")
            st.text_area(
                "Document content",
                value=text,
                height=250,
                disabled=True,
            )
        else:
            st.warning(
                "No text was extracted. Images and scanned PDFs "
                "may require OCR, which is not included in this lesson."
            )

    st.divider()
    st.subheader("Uploaded Documents")
    try:
        records = load_document_index()
    except ValueError as error:
        st.error(str(error))
        return

    if not records:
        st.info("No documents have been uploaded yet.")
        return

    for record in records:
        with st.container(border=True):
            st.write(f"**{record['original_filename']}**")
            st.caption(
                f"{record['category']} | {record['id']} | "
                f"{record['size_bytes']} bytes"
            )
            st.caption(f"Stored as {record['stored_filename']}")
