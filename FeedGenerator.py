from urllib.error import HTTPError

import bs4.element
from pyopenmensa.feed import LazyBuilder
from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import date, timedelta

mensa = LazyBuilder()


def getMealsForDay(day: str):
    if date.fromisoformat(day).weekday() > 4:  # Saturday or Sunday
        mensa.setDayClosed(date.fromisoformat(day))
        return True

    try:
        url = "https://www.stw-greifswald.de/essen/speiseplan/mensa-stralsund?datum=" + day
        html = urlopen(url).read()
    except HTTPError as e:
        if e.code == 404:
            mensa.setDayClosed(date.fromisoformat(day))
            return True
        return False
    soup = BeautifulSoup(html, 'html.parser')

    if mensa.legendData is None:
        for div in soup.find_all('div', {'class': 'col-12'}):
            for child in div.children:
                if type(child) == bs4.element.Tag and child.text == 'Kennzeichnungspflichtige Zusatzstoffe':
                    mensa.legendData = {}
                    for item in div.find_all("li"):
                        mensa.legendData[item.contents[0].text] = item.contents[1].text

    for table in soup.find_all('table', {'class': 'menu-table'}):
        category = ''
        for tr in table.find_all('tr'):
            if 'class' in tr.attrs and "menu-table-row" in tr.attrs['class']:
                category = tr.find("td").text.strip()
            else:
                meal = tr.find("td").text.strip()
                prices = [_p.text.strip().replace("\xa0", " ") for _p in tr.find_all("td")[-3:]]
                if '' in prices:
                    mensa.addMeal(day, category, meal)
                else:
                    mensa.addMeal(day, category, meal, prices=prices, roles=['student', 'employee', 'other'])
    return mensa.hasMealsFor(date.fromisoformat(day))


def generateFull():
    day = date.today()
    while getMealsForDay(day.isoformat())\
            and day <= date.today() + timedelta(days=14):
        day = day + timedelta(days=1)

    with open('full.xml', 'w') as fd:
        fd.write(mensa.toXMLFeed())


if __name__ == "__main__":
    generateFull()
