#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask.globals import session
from flask.json import jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#Many_to_Many_Relationship

class Show(db.Model):
  __tablename__='shows'
  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id' ,ondelete='CASCADE'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey(
      'venues.id', ondelete='CASCADE'), nullable=False)
  start_time=db.Column(db.DateTime , nullable=False)
  artist=db.relationship('Artist' , backref='shows')
  venue = db.relationship('Venue', backref='shows')
  def with_artist(self):
    return {
      'artist_id':self.artist_id ,
      'artist_name':self.artist.name,
      'artist_image_link':self.artist.image_link,
      'start_time':self.start_time.strftime('%Y-%m-%d %H:%M:%S')
    }
  def with_venue(self):
    return {
      'venue_id':self.venue_id ,
      'venue_name':self.venue.name,
      'venue_image_link':self.venue.image_link,
      'start_time':self.start_time.strftime('%Y-%m-%d %H:%M:%S')
    }


class Venue(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres=db.Column(db.String(120))
    seeking_talent=db.Column(db.Boolean)
    seeking_description=db.Column(db.String(300))
    website=db.Column(db.String(200))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    artists = db.relationship('Artist', secondary='shows',
      backref=db.backref('venues', lazy=True))
    def __repr__(self):
      return f"<Venue {self.name} , {self.id}>"

class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website=db.Column(db.String(200))
    seeking_venue = db.Column(db.Boolean)
    seeking_description=db.Column(db.String(150))
    facebook_link = db.Column(db.String(120))
    
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data=[]
  venus = Venue.query.order_by(Venue.state,Venue.city).all()
  if len(venus) == 0:
    flash('Venues are empty !! , please add some venues :)', 'warning')
    return redirect(url_for('index'))
  prev_city=None
  prev_state=None
  for venue in venus:
    venue_data={
      'id':venue.id ,
      'name' : venue.name ,
      'num_upcoming_shows' : len(list(filter(lambda x : x.start_time > datetime.today() , venue.shows)))
    }
    if prev_city==venue.city and venue.state==prev_state:
      tmp['venues'].append(venue_data)
    else:
      if prev_city is not None :
        data.append(tmp)
      tmp = {}
      tmp['city']=venue.city
      tmp['state']=venue.state
      tmp['venues']=[venue_data]
    prev_state=venue.state
    prev_city=venue.city
  data.append(tmp)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  search_term=request.form['search_term']
  venues=Venue.query.filter(Venue.name.ilike('%'+search_term+'%')).all()
  response={}
  response['count']=len(venues)
  response['data']=[]
  for venue in venues:
    temp={}
    temp['id']=venue.id
    temp['name']=venue.name
    temp['num_upcoming_shows']=len (list (filter(lambda x : x.start_time > datetime.today() ,venue.shows)))
    response['data'].append(temp)
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data={}
  venue = Venue.query.filter_by(id=venue_id).first()
  data['id']=venue.id
  data['name']=venue.name
  data['genres'] = venue.genres[1:len(venue.genres)-1].split(',')
  data['address'] = venue.address
  data['city']=venue.city
  data['state']=venue.state
  data['phone'] = venue.phone
  data['website']=venue.website
  data['facebook_link']=venue.facebook_link
  data['seeking_talent']=venue.seeking_talent
  if venue.seeking_talent :
    data['seeking_description'] = venue.seeking_description
  data['image_link']=venue.image_link
  past_shows = list( filter( lambda x: x.start_time < datetime.today(), venue.shows ) )
  upcoming_shows = list( filter( lambda x: x.start_time >= datetime.today(), venue.shows ) )
  past_shows = list( map( lambda x: x.with_artist(), past_shows) )
  upcoming_shows = list(map(lambda x: x.with_artist(), upcoming_shows))
  data['past_shows']=past_shows
  data['upcoming_shows']=upcoming_shows
  data['past_shows_count']=len(past_shows)
  data['upcoming_shows_count']=len(upcoming_shows)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error=False
  try:
    name=request.form['name']
    city=request.form['city']
    state=request.form['state']
    address=request.form['address']
    phone=request.form['phone']
    genres = request.form.getlist('genres')
    if request.form.get('seeking_talent') :
      seeking_talent=True
    else :
      seeking_talent = False
    seeking_description=request.form.get('seeking_description')
    image_link=request.form['image_link']
    facebook_link=request.form['facebook_link']
    website=request.form['website']
    ven = Venue.query.filter_by(name=name, city=city, state=state,address=address).all()
    if len(ven) >=1:
      flash(request.form['name'] + ' Already exist in venues','warning')
      return render_template('pages/home.html')
    venue=Venue(name=name , city=city , state=state , address=address,
    phone=phone , genres=genres ,
    seeking_talent=seeking_talent,seeking_description=seeking_description, website=website ,image_link=image_link, 
    facebook_link=facebook_link)
    db.session.add(venue)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' was not successfully listed!','danger')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!','info')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  status=200
  success=True
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    success=False
    status=500
    db.session.rollback()
    print( sys.exc_info() )
  finally:
    db.session.close()
  if not success:
    flash('An error occurred. Venue was not successfully Deleted!','danger')
  else:
    flash('Venue was successfully Deleted!', 'info')
  return jsonify({'success' :success},status)

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  status=200
  success=True
  try:
    Artist.query.filter_by(id=artist_id).delete()
    db.session.commit()
  except:
    success=False
    status=500
    db.session.rollback()
    print( sys.exc_info() )
  finally:
    db.session.close()
  if not success:
    flash('An error occurred. Artist was not successfully Deleted!','danger')
  else:
    flash('Artist was successfully Deleted!', 'info')
  return jsonify({'success' :success},status)


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists=Artist.query.all()
  if len(artists) == 0:
    flash('Artists are empty !!, please add some artists :) ', 'warning')
    return redirect(url_for('index'))
  data=[]
  for artist in artists:
    temp={}
    temp['id']=artist.id
    temp['name']=artist.name
    data.append(temp)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term=request.form['search_term']
  venues=Venue.query.filter(Venue.name.ilike('%'+search_term+'%')).all()
  response={}
  response['count']=len(venues)
  response['data']=[]
  for venue in venues:
    temp={}
    temp['id']=venue.id
    temp['name']=venue.name
    temp['num_upcoming_shows']=len (list (filter (lambda x : x.start_time > datetime.today() , venue.shows)))
    response['data'].append(temp)
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data = {}
  artist = Artist.query.filter_by(id=artist_id).first()
  data['id'] = artist.id
  data['name'] = artist.name
  data['genres'] = artist.genres[1:len(artist.genres)-1].split(',')
  data['city'] = artist.city
  data['state'] = artist.state
  data['phone'] = artist.phone
  data['website'] = artist.website
  data['facebook_link'] = artist.facebook_link
  data['seeking_venue'] = artist.seeking_venue
  if artist.seeking_venue:
    data['seeking_description'] = artist.seeking_description
  data['image_link'] = artist.image_link
  past_shows=list (filter(lambda x : x.start_time < datetime.today() , artist.shows))
  upcoming_shows=list (filter(lambda x : x.start_time > datetime.today() ,artist.shows))
  
  past_shows=list(map(lambda x: x.with_venue(),past_shows))
  upcoming_shows=list(map (lambda x : x.with_venue() ,upcoming_shows))
  data['past_shows']=past_shows
  data['upcoming_shows']=upcoming_shows
  data['past_shows_count']=len(past_shows)
  data['upcoming_shows_count']=len(upcoming_shows)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist=Artist.query.get(artist_id)
  data={}
  data['id'] = artist.id
  data['name'] = artist.name
  data['genres'] = artist.genres[1:len(artist.genres)-1].split(',')
  data['city'] = artist.city
  data['state'] = artist.state
  data['phone'] = artist.phone
  data['website'] = artist.website
  data['facebook_link'] = artist.facebook_link
  data['seeking_venue'] = artist.seeking_venue
  if artist.seeking_venue:
    data['seeking_description'] = artist.seeking_description
  data['image_link'] = artist.image_link
  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error=False
  try:
    artist =Artist.query.get(artist_id)
    artist.name= request.form['name']
    artist.city=request.form['city']
    artist.state = request.form['state']
    artist.phone=request.form['phone']    
    artist.genres = request.form.getlist('genres')
    if request.form.get('seeking_venue'):
      artist.seeking_venue = True
    else:
      artist.seeking_venue = False
    artist.seeking_description = request.form.get('seeking_description')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    db.session.commit()
  except:
    db.session.rollback()
    error=True
  finally:
    db.session.close()
  if error:
    flash('An error occurred cant edit Artist' + artist.name,'danger')
    return redirect(url_for('index'))
  else :
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  data = {}
  data['id'] = venue.id
  data['name'] = venue.name
  data['genres'] = venue.genres[1:len(venue.genres)-1].split(',')
  data['address']=venue.address
  data['city'] = venue.city
  data['state'] = venue.state
  data['phone'] = venue.phone
  data['website'] = venue.website
  data['facebook_link'] = venue.facebook_link
  data['seeking_talent'] = venue.seeking_talent
  if venue.seeking_talent:
    data['seeking_description'] = venue.seeking_description
  data['image_link'] = venue.image_link
  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.address=request.form['address']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    if request.form.get('seeking_talent'):
      venue.seeking_talent = True
    else:
      venue.seeking_talent = False
    venue.seeking_description = request.form.get('seeking_description')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if error:
    flash('An error occurred cant edit venue' + venue.name, 'danger')
    return redirect(url_for('index'))
  else:
    return redirect(url_for('show_venue', venue_id=venue_id))
  

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error=False
  try:
    name=request.form['name']
    city=request.form['city']
    state=request.form['state']
    phone=request.form['phone']    
    genres = request.form.getlist('genres')
    if request.form.get('seeking_venue'):
      seeking_venue = True
    else:
      seeking_venue = False
    seeking_description = request.form.get('seeking_description')
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    art = Artist.query.filter_by(
        name=name, city=city, state=state,phone=phone).all()
    if len(art) >= 1:
      flash(request.form['name'] + 'Already exist in artists', 'warning')
      return render_template('pages/home.html')
    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, seeking_venue=seeking_venue,
    seeking_description=seeking_description,image_link=image_link,facebook_link=facebook_link,website=website)
    db.session.add(artist)
    db.session.commit()
  except:
    db.session.rollback()
    error=True
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.' ,'danger')
  else:
    flash('Artist ' + request.form['name'] +
            ' was successfully listed!', 'info')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows=Show.query.all()
  if len(shows)==0:
    flash('There are no shows please add some shows','warning')
    return redirect(url_for('index'))
  data=[]
  for show in shows:
    show_data={}
    show_data['venue_id'] = show.venue_id
    show_data['venue_name']=show.venue.name
    show_data['artist_id'] = show.artist_id
    show_data['artist_name'] = show.artist.name
    show_data['artist_image_link'] = show.artist.image_link
    show_data['start_time'] = show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    data.append(show_data)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error=False
  try:
    show=Show()
    show.artist_id=request.form['artist_id']
    show.venue_id=request.form['venue_id']
    show.start_time=request.form['start_time']
    db.session.add(show)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Show could not be listed.' ,'danger')
  else :
      flash('Show was successfully listed!' ,'info')
  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
