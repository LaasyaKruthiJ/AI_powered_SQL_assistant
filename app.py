from flask import Flask, request, send_from_directory
import time
from modal import full_chain

app = Flask(__name__, static_folder='.', template_folder='.')

@app.route("/", methods=["GET"])
def index():
    return send_from_directory('.', 'index.html')

@app.route("/style.css")
def style():
    return send_from_directory('.', 'style.css')


@app.route("/get-result", methods=["POST"])
def get_result():
    query = request.form.get("question")
    if query:
        start_time = time.time()
        try:
            response = full_chain.invoke({"question": query})
            answer = response
            execution_time = round(time.time() - start_time, 2)
        except Exception as e:
            return {"error": f"Error: {str(e)}"}
        return {"query": query, "answer": answer, "execution_time": execution_time}
    return {"error": "No question provided"}

if __name__ == "__main__":
    app.run(debug=True)
