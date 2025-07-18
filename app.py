from flask import Flask, render_template, request
from modal import full_chain 
import time

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    answer = None
    query = None
    sql_query = None
    execution_time = None

    if request.method == "POST":
        query = request.form.get("question")
        if query:
            start_time = time.time()
            try:
                response = full_chain.invoke({"question": query})
                answer = response
                execution_time = round(time.time() - start_time, 2)
            except Exception as e:
                answer = f"Error: {str(e)}"

    return render_template("index.html", answer=answer, query=query, execution_time=execution_time)

if __name__ == "__main__":
    app.run(debug=True)
