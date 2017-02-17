import requests, datetime
import sys
from bs4 import BeautifulSoup
from captcha_solver import CaptchaSolver

def login(s):
    s.get('https://teleservices.paris.fr/srtm/deconnexionAccueil.action')
    payload = {'login': 'LOGIN', 'password': 'PASSWORD'}
    rep = s.post('https://teleservices.paris.fr/srtm/authentificationConnexion.action', data=payload, allow_redirects=True)
    if len(rep.cookies) == 0:
        raise Exception('Login fail')

def listBooking(s):
    today = datetime.date.today()
    next_wenesday = today + datetime.timedelta( (2-today.weekday()) % 7 )
    payload = {
        'provenanceCriteres':'true',
        'actionInterne': 'recherche',
        'arrondissement': 20,
        'dateDispo': next_wenesday.strftime("%d/%m/%Y"),
        'plageHoraireDispo': '18@21'
    }
    rep = s.post('https://teleservices.paris.fr/srtm/reservationCreneauListe.action', data=payload)

    list_booking = []
    soup = BeautifulSoup(rep.text, 'html.parser')
    table = soup.find('table', {'class': 'normal'})
    lignes = table.find_all('tr', {'class': 'odd'})
    for ligne in lignes:
        data = ligne.find_all('td')
        href = data[6].find('a').attrs['href']
        payload = href.split("'")[1]
        booking = {
            'short': data[0].text,
            'date': data[2].text,
            'hour': data[3].text[:2],
            'payload': payload
        }
        list_booking.append(booking)

    return list_booking

def book(s, list_booking):
    to_book = None
    for booking in list_booking:
        if booking['hour'] == '20':
            to_book = booking
            break

    if to_book != None:
        payload = {'cle': to_book['payload']}
        rep = s.post('https://teleservices.paris.fr/srtm/reservationCreneauReserver.action', data=payload)

        captcha = s.get('https://teleservices.paris.fr/srtm/ImageCaptcha').text.encode('ISO-8859-1')
        solver = CaptchaSolver('browser')
        payload['jcaptcha_reponse'] = solver.solve_captcha(captcha)
        payload['valider'] = 'ENREGISTRER'
        rep = s.post('https://teleservices.paris.fr/srtm/ReservationCreneauValidationForm.action', data=payload)

        if rep.ok:
            print 'Book done in %s the %s at %sh' % (to_book['short'], to_book['date'], to_book['hour'])
        else:
            print 'Fail booking'
    else:
        print 'No book found'

if __name__ == '__main__':
    with requests.Session() as s:
        login(s)
        book(s, listBooking(s))




