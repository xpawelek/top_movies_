from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.numeric import FloatField, DecimalField
from wtforms.validators import DataRequired, NumberRange
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(500), nullable=True)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)

with app.app_context():
    db.create_all()

class RateMovieForm(FlaskForm):
    rating = DecimalField(label="Your rating out of 10:", places=1, validators=[DataRequired(), NumberRange(min=0, max=10)])
    review = StringField(label="Your review: ", validators=[DataRequired()])
    button = SubmitField(label="Done")

class AddMovieForm(FlaskForm):
    movie_name = StringField("Movie title: ", validators=[DataRequired()])
    button = SubmitField(label="Add movie")
@app.route("/")
def home():
    with app.app_context():
        movies = Movie.query.order_by(Movie.rating.desc()).all()
        counter = 1
        for movie in movies:
            movie_to_update = db.session.execute(db.Select(Movie).where(Movie.id == movie.id)).scalar()
            movie_to_update.ranking = counter
            db.session.commit()
            counter += 1
        movies = Movie.query.order_by(Movie.ranking.desc()).all()

    return render_template("index.html", movies=movies)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        movie_name = request.form["movie_name"]
        url = "https://api.themoviedb.org/3/search/movie"

        headers = {
            "accept": "application/json",
        }
        params = {
            "query": movie_name,
            "api_key": "09c4a093b3b331e564b93f3de2d668d8"
        }

        response = requests.get(url, headers=headers, params=params).json()

        movies = response["results"]
        return render_template("select.html", movies=movies)

    form = AddMovieForm()
    return render_template("add.html", form=form)
@app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
def edit(movie_id):
    if request.method == "POST":
        with app.app_context():
            movie_to_update = db.session.execute(db.Select(Movie).where(Movie.id == movie_id)).scalar()
            movie_to_update.rating = request.form.get("rating")
            movie_to_update.review = request.form.get("review")
            db.session.commit()
            return redirect(url_for("home"))

    movie = db.session.execute(db.Select(Movie).where(Movie.id == movie_id)).scalar()
    form = RateMovieForm()
    form.rating.data = movie.rating
    form.review.data = movie.review
    return render_template("edit.html", id=movie_id, form=form)

@app.route("/delete/<int:movie_id>")
def delete(movie_id):
    with app.app_context():
        Movie.query.filter_by(id=movie_id).delete()
        db.session.commit()

    return redirect(url_for("home"))

@app.route("/find")
def find():
    api_movie_id = request.args.get("api_movie_id")

    url = f"https://api.themoviedb.org/3/movie/{api_movie_id}"

    headers = {
        "accept": "application/json",
    }
    params = {
        "api_key": "09c4a093b3b331e564b93f3de2d668d8",
        "language": "en-US"
    }

    response = requests.get(url, headers=headers, params=params).json()
    title = response["original_title"]
    img_url = f"https://image.tmdb.org/t/p/w500{response["poster_path"]}"
    year = response["release_date"].split("-")[0]
    description = response["overview"]

    movie = Movie(title=title, year=year, description=description, img_url=img_url)
    db.session.add(movie)
    db.session.commit()

    return redirect(url_for("edit", movie_id=movie.id))

if __name__ == '__main__':
    app.run(debug=True)
