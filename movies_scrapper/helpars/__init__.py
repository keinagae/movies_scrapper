def find_relevant_year(shows, project):
    year = project['produktion_jahr'].lower()
    dmb_year = project['dmbProduktionsJahr'].lower()
    flag = ""
    found_project = {}
    if year:
        year = year.split("/")[0].strip()
        try:
            year = int(year)
        except ValueError:
            year = 0
    else:
        year = 0

    if dmb_year:
        dmb_year = dmb_year.split("/")[0].strip()
        try:
            dmb_year = int(dmb_year)
        except ValueError:
            dmb_year = 0
    else:
        dmb_year = 0
    year_similar = list(
        filter(
            lambda show: all([
                show['year'],
                any(
                    [
                        year in show['year'],
                        dmb_year in show['year']
                    ]
                )
            ]),
            shows
        )
    )
    if year_similar:
        found_project = year_similar[0]
        flag = "year"
    else:
        year_similar = list(
            filter(
                lambda show: all([
                    show['year'],
                    any(
                        [
                            year + 1 in show['year'],
                            dmb_year + 1 in show['year'],
                        ]
                    )
                ]),
                shows
            )
        )
        if year_similar:
            found_project = year_similar[0]
            flag = "year inc"
        else:
            year_similar = list(
                filter(
                    lambda show: all([
                        show['year'],
                        any(
                            [
                                year - 1 in show['year'],
                                dmb_year - 1 in show['year'],
                            ]
                        )
                    ]),
                    shows
                )
            )
            if year_similar:
                found_project = year_similar[0]
                flag = "year dec"
    return found_project, flag


def find_relevant_year_show_json(shows, project):
    year = project['year'].lower()
    flag = ""
    found_project = {}
    if year:
        year = year.split("/")[0].strip()
        try:
            year = int(year)
        except ValueError:
            year = 0
    else:
        year = 0

    year_similar = list(
        filter(
            lambda show: all([
                show['year'],
                year in show['year'],
            ]),
            shows
        )
    )
    if year_similar:
        found_project = year_similar[0]
        flag = "year"
    else:
        year_similar = list(
            filter(
                lambda show: all([
                    show['year'],
                    year + 1 in show['year'],

                ]),
                shows
            )
        )
        if year_similar:
            found_project = year_similar[0]
            flag = "year inc"
        else:
            year_similar = list(
                filter(
                    lambda show: all([
                        show['year'],
                        year - 1 in show['year'],
                    ]),
                    shows
                )
            )
            if year_similar:
                found_project = year_similar[0]
                flag = "year dec"
    return found_project, flag