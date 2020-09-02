""" Pełzacz zwracający wolne miejsca na dowolny seans w dowolnym kinie
    sieci Helios w Polsce """

import re
import requests
from bs4 import BeautifulSoup as Bs


class Helios:

    SESSION = requests.Session()

    def __enter__(self):
        print("Start programu")
        return Helios()

    @classmethod
    def show_cinemas(cls) -> dict:
        """ Wyświetla dostępne kina Helios w Polsce """

        result = {}
        page_text = cls.SESSION.get("https://www.helios.pl/").text
        cinemas_list = Bs(page_text, "html.parser").findAll(
            "li", attrs={"data-location": True}
        )
        for index, cinema in enumerate(cinemas_list):
            try:
                result[index] = [
                    cinema.text.strip(),
                    "https://www.helios.pl" + cinema.a.get("href"),
                ]
            except AttributeError:  # dla wykluczenia kin, które są w budowie
                continue
        return result

    @classmethod
    def choose_cinema(cls, cinema_url: str) -> str:
        """ Umożliwia wybranie kina i zwraca link z repertuarem
            na dzień dzisiejszy
        """

        result = cls.SESSION.get(cinema_url).text
        return "https://helios.pl" + Bs(result, "html.parser").find(
            "a", {"class": "slide-link"}
        ).get("href")

    @classmethod
    def show_reportoire_and_calendar(cls, url: str) -> tuple:
        """ Zwraca w krotce dwa słowniki: jeden dni, na które są już dostępne
            seanse wraz z linkami do każdego dnia, drugi to seans z godzinami

        Przykładowy wynik:
        (
         {'02':
          (
           'https://www.helios.pl//37,Belchatow/Repertuar/index/dzien/0/kino/37',
           ['Śr', '02', 'wrz']
          )
         },
         {
          'NOWI MUTANCI / napisy': [['15:30', '18:00']
         }
        )

        """
        movies = {}
        calendar = {}
        source_page = requests.get(url).text
        seance_gallery = Bs(source_page, "html.parser").findAll(
            "li", {"class": "seance"}
        )
        for data in seance_gallery:
            movie = data.find("a", {"class": "movie-link"}).text.strip()
            movies[movie] = []
            for time_a in data.findAll("a", {"class": "hour-link"}):
                if "fancybox-reservation" in time_a.get("class"):
                    movies[movie].append(
                        [time_a.text, "https://helios.pl" + time_a.get("href"),]
                    )
                else:
                    movies[movie].append(
                        [time_a.text, None]
                    )
        days = (
            Bs(source_page, "html.parser")
            .find("ul", {"class": "days"})
            .findAll("a", {"class": "day-link"})
        )
        for item in days:
            href = item.get("href")
            days = item.text.strip().split("\n")
            if item.has_attr("href"):
                calendar[days[1]] = ("https://www.helios.pl/" + href, days)
        return calendar, movies

    @classmethod
    def generate_seats(cls, seance_url: str) -> list:
        """
        Zwraca listę z oznaczeniami miejsc, które następnie
        przerobię na nieaktywne przyciski, pierwsza pozycja w liście
        to dane dot. seansu, pozostałe są miejscami.

        """

        result = []
        api_url = "https://bilety.helios.pl/msi/"
        token = re.findall(r"seans/(.*?)/", seance_url)[0]
        cls.SESSION.get(api_url + "event/" + token)
        cls.SESSION.get(api_url + "Order?id=0")
        cinema_room = cls.SESSION.get(api_url + "PvSeat").text
        header_json = cls.SESSION.get(api_url + "getjsondata").json()["cinevent"]
        result.append(
            [header_json["cinemaname"], header_json["title"], header_json["formatdate"]]
        )
        rows = Bs(cinema_room, "html.parser").findAll("div", {"class": "s-row"})
        one_row = []
        for row in rows:
            seats = row.findAll("div", {"class": "seat"})
            for seat in seats:
                # Fatalnie to wygląda, sporo zagnieżdżeń, muszę to jakoś zmodyfikować
                if "blank" in seat.get("class"):
                    one_row.append(["", "#FFFFFF", ""])
                if "nh" and "icon-inv" in seat.get("class"):
                    one_row.append(["", "#0000FF", ""])
                if "nn" and "icon-blo" in seat.get("class"):
                    if "sofa" in seat.get("class"):
                        one_row.append(["", "#FFCCCB", "sofa"])
                    else:
                        one_row.append(["", "#FF0000", ""])
                if "active" in seat.get("class"):
                    text = '{}'.format(seat.text if len(seat.text.strip()) == 2 else "0" + seat.text)
                    if "sofa" in seat.get("class"):
                        one_row.append([text, "#00BFFF", "sofa"])
                    else:
                        one_row.append([text, "#fb0", ""]
                    )
            result.append(one_row)
            one_row = []
        return result


    def __exit__(self, exc_type, exc_value, exc_traceback):
        print("Koniec programu")
        self.SESSION.close()
