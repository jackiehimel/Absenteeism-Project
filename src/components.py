import streamlit.components.v1 as components

def handle_select_changes():
    components.html(
        """
        <script>
        window.addEventListener('message', function(e) {
            const data = e.data;
            if (data && data.key) {
                window.parent.Streamlit.setSessionState(data);
            }
        });
        </script>
        """,
        height=0,
    )
