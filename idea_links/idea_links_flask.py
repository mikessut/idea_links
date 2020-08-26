
from flask import render_template, Flask, request
from idea_links.idea_links import Idea
import idea_links.idea_links as mm
app = Flask(__name__)


@app.route('/')
def index():
    print(request.args.get("doc_id", None))
    if request.args.get("doc_id", None) is None:
        i = Idea.from_doc_id(1)
    else:
        i = Idea.from_doc_id(request.args.get("doc_id", type=int))
    return render_template('idea_link.html', idea=i)


@app.route("/search")
def search():
    results = mm.search(request.args.get("search_txt"))
    if len(results) == 0:
        return "No results"
    return render_template('search_results.html', results=results)


@app.route("/edit")
def edit():
    parents = request.args.get("parents", None, type=list)
    print("parents", parents)
    tmp = dict(request.args)
    for k in Idea.relation_fields:
        if k in tmp.keys():
            tmp[k] = eval(tmp[k])
    print(tmp)

    if request.args.get("doc_id", None, type=int) is not None:
        i = Idea.from_doc_id(request.args.get("doc_id", None, type=int))
    else:
        i = Idea(**tmp)
    #i.add_parent(Idea.from_doc_id(parent_doc_id))
    return render_template("edit.html", idea=i)


@app.route("/save", methods=['POST'])
def save():
    print(request.values)
    tmp = dict(request.values)
    for k in Idea.relation_fields:
        tmp[k] = eval(tmp[k])
    print(tmp)
    i = Idea(**tmp)
    try:
        i.doc_id = int(request.values['doc_id'])
    except ValueError:
        print(f"Unable to set doc_id: {request.values['doc_id']}")
        i.doc_id = None
    i.save()
    i.check_relations()
    return f"saved<br><a href=/?doc_id={i.doc_id}>{i.short_txt}</a>"


if __name__ == '__main__':
    app.run(debug=False)


