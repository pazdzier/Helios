""" GUI w Tkinter do obsługi danych zbieranych z witryny helios.pl """

import tkinter as tk
from tkinter import Canvas
from scrapper import Helios


class StartPage:
    """ Strona startowa - pokazuje w polsce kina Helios w przyciskach
        kliknięcie w przycisk otwiera nowe okno z podglądem repertuary
        na dzisiaj """

    def __init__(self, master, helios):
        self.master = master
        self.helios = helios
        self.frame = tk.Frame(self.master)
        self.frame.grid()
        self.show_cinemas()


    def show_cinemas(self):
        """ Pokazuje dostępne kina Helios w Polsce """

        cinemas = self.helios.show_cinemas()
        tk.Label(self.frame, text="Wybierz kino").grid(pady=5, padx=5, columnspan=4)
        row = 1
        column = 0
        for index, key in enumerate(cinemas, 5):
            tk.Button(
                self.frame,
                width=30,
                text=cinemas[key][0],
                command=lambda key=key: self.open_cinema(cinemas[key][1]),
            ).grid(row=row, column=column, pady=1, padx=1)
            column += 1
            if index % 4 == 0:
                row += 1
                column = 0

    def open_cinema(self, selected_cinema):
        """ Otwiera nowe okno i generuje w nim podgląd ramówki na dzień dzisiejszy """

        url = self.helios.choose_cinema(selected_cinema)
        new_window = tk.Toplevel(self.master)
        CinemaPage(new_window, self.helios, url)


class CinemaPage:
    """ Zwraca ramówkę wybranego kina, umożliwia wygenerowanie wolnych miejsc
        siedzących jak również wybranie innych dni. Domyślnie uruchamia się
        widok dnia dzisiejszego """

    def __init__(self, master, helios, url):
        self.master = master
        self.url = url
        self.helios = helios
        self.days_frame = tk.Frame(self.master)
        self.days_frame.grid()
        self.seanse_list_frame = tk.Frame(self.master)
        self.seanse_list_frame.grid(sticky=tk.W, pady=5)
        self.show(url)

    def show(self, url):
        calendar, movies = self.helios.show_reportoire_and_calendar(url)
        for index, item in enumerate(calendar):
            url = calendar[item][0]
            tk.Button(
                self.days_frame,
                width=10,
                text="\n".join(calendar[item][1]),
                command=lambda url=url: self.change_day(url),
            ).grid(row=0, column=index)
        tk.Label(self.seanse_list_frame, height=2, text="ramówka").grid(
            columnspan=10, column=1, row=0
        )
        for index, item in enumerate(movies, 1):
            tk.Label(self.seanse_list_frame, anchor="w", text=item).grid(
                row=index, column=1, columnspan=3, sticky=tk.W
            )
            for second_index, time in enumerate(movies[item], 1):
                if time[1]:
                    tk.Button(
                        self.seanse_list_frame,
                        width=4,
                        fg="#0000FF",
                        text=time[0],
                        command=lambda time=time: self.show_seance(time[1]),
                    ).grid(row=index, column=4 + second_index, sticky=tk.W, padx=1)
                else:
                    tk.Button(
                        self.seanse_list_frame,
                        state=tk.DISABLED,
                        width=4,
                        text=time[0],
                    ).grid(row=index, column=4 + second_index, sticky=tk.W, padx=1)

    def show_seance(self, seance_url):
        """ Otwiera nowe okno, w którym będzie wygenerowany podgląd sali
            kinowej """

        new_window = tk.Toplevel(self.master)
        ShowSeanceSeats(new_window, self.helios, seance_url)

    def change_day(self, day_url):
        """ Umożliwia zmianę wyświetlanego dnia na inny """
        for widget in self.seanse_list_frame.winfo_children():
            widget.destroy()
        self.show(day_url)


class ShowSeanceSeats:
    """ Klasa umożliwia w trzecim oknie podgląd kina wraz z informacją o
        wolnych / zajętych miejscah """

    def __init__(self, master, helios, seance_url=None):
        self.master = master
        self.helios = helios
        self.seance_url = seance_url
        self.seats_frame = tk.Frame(self.master, bd=1)
        self.seats_frame.grid()
        self.generate_seats()

    def generate_seats(self):
        """
        Generuje widok dostępnych miejsc z listy wartości
        index 0 - dane dot. seansu, index[1:] to są rzędy w sali kinowej
        """
        result = self.helios.generate_seats(self.seance_url)
        for index, cinema_info in enumerate(result[0]):
            tk.Label(self.seats_frame, text=cinema_info).grid(
                row=index, column=0, columnspan=10, sticky=tk.W
            )

        canvas = Canvas(self.seats_frame, width=1400, height=1000)
        x1, y1, x2, y2 = (20, 10, 40, 30)
        for row in result[1:]:
            sofa = False
            for seat in row:
                canvas.create_rectangle(x1, y1, x2, y2, outline=seat[1], fill=seat[1])
                canvas.create_text(x1+4, y1+3, anchor=tk.NW, text=seat[0])
                if "sofa" in seat[2] and not sofa:
                    sofa = True
                    x1 += 20
                    x2 += 20
                else:
                    sofa = False
                    x1 += 30
                    x2 += 30
            x1 = 20
            x2 = 40
            y1 += 30
            y2 += 30
        canvas.create_text(x1, y1, anchor=tk.NW, text="Legenda:")
        canvas.create_rectangle(x1, y1+30, x2, y2+30, outline="#fb0", fill="#fb0")
        canvas.create_text(x1+30, y1+33, anchor=tk.NW, text="Miejsce wolne")
        canvas.create_rectangle(x1, y1+60, x2, y2+60, outline="#FF0000", fill="#FF0000")
        canvas.create_text(x1+30, y1+63, anchor=tk.NW, text="Miejsce zajęte")
        canvas.create_rectangle(x1, y1+90, x2, y2+90, outline="#00BFFF", fill="#00BFFF")
        canvas.create_text(x1+30, y1+93, anchor=tk.NW, text="Wolna Sofa")
        canvas.create_rectangle(x1, y1+120, x2, y2+120, outline="#FFCCCB", fill="#FFCCCB")
        canvas.create_text(x1+30, y1+123, anchor=tk.NW, text="Zajęta Sofa")
        canvas.create_rectangle(x1, y1+150, x2, y2+150, outline="#0000FF", fill="#0000FF")
        canvas.create_text(x1+30, y1+153, anchor=tk.NW, text="Miejsce dla niepełnosprawnych")
        canvas.grid()





def main():
    """ Uruchamia program """
    with Helios() as helios:
        root = tk.Tk()
        StartPage(root, helios)
        root.mainloop()


if __name__ == "__main__":
    main()
