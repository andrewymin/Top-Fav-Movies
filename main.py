from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

TMDB_URL = 'https://api.themoviedb.org/3/search/movie?'
API_KEY = os.getenv('tmdb_api_key')
TMDB_BEARER_TOKEN = os.getenv('tmdb_access_token')
SQL_SECRET_KEY = os.getenv('sql_secret_key')

app = Flask(__name__)
app.config['SECRET_KEY'] = SQL_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)


class RateMovieForm(FlaskForm):
    rating = StringField(label='Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField(label='Your Review', validators=[DataRequired()])
    submit = SubmitField(label='Done')


class AddMovieForm(FlaskForm):
    title = StringField(label='Movie Title', validators=[DataRequired()])
    submit = SubmitField(label='Add Movie')


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Movie{self.title}>'


if not os.path.isfile("sqlite:///movie-collection.db"):
    db.create_all()


@app.route("/")
def home():
    # Ordering all movies by rating, automatically orders (top to bottom = lowest to highest) number
    all_movies = Movie.query.order_by(Movie.rating).all()
    # looping through number of movies, from 0-number of movies/items
    for i in range(len(all_movies)):
        # Starting at 0 as range does, looping through all_movies index and making (ranking - index number)
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    # Using flask-form to get data from the inputted forms
    # Don't forget to import "bootstrap/wtf.html" as wtf in {%%} at the html top file
    form = RateMovieForm()
    edit_id = request.args.get('id')
    if form.validate_on_submit():
        # Flask from syntax to get individual form data
        new_rating = float(form.rating.data)
        new_review = form.review.data

        # Getting the id from the html page and using that to update the sql file
        movie_to_update = Movie.query.get(edit_id)
        movie_to_update.rating = new_rating
        movie_to_update.review = new_review
        db.session.commit()
        # Once done updating redirecting the page to the home page
        return redirect(url_for('home'))

    return render_template('edit.html', form=form)


@app.route('/delete')
def delete():
    delete_id = request.args.get('id')
    movie_to_delete = Movie.query.get(delete_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        tmdb_params = {
            "api_key": API_KEY,
            "query": form.title.data
        }
        header = {
            'Authorization': f'Bearer {TMDB_BEARER_TOKEN}',
            'Content-Type': 'application/json;charset=utf-8',
        }
        response = requests.get(TMDB_URL, params=tmdb_params, headers=header)
        response.raise_for_status()
        movie_list = response.json()["results"]
        return render_template('select.html', movies=movie_list)
    return render_template('add.html', form=form)


@app.route('/new_movie')
def new_movie():
    movie_id = request.args.get('id')
    response = requests.get(url=f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}')
    response.raise_for_status()
    movie_details = response.json()
    title = movie_details['title']
    year = movie_details['release_date']
    overview = movie_details['overview']
    img_url = 'https://image.tmdb.org/t/p/w500/' + movie_details['poster_path']
    new_movie_top = Movie(
        title=title,
        year=year,
        description=overview,
        img_url=img_url,
    )
    db.session.add(new_movie_top)
    db.session.commit()
    new_added_movie = Movie.query.filter_by(title=title).first()
    movie_id = new_added_movie.id
    return redirect(url_for('edit', id=movie_id))


if __name__ == '__main__':
    app.run(debug=True)
    # app.run()
