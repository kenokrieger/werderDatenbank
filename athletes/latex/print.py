from pylatex import Document, Section, LongTable, MultiColumn, NewLine,\
    MediumText, LargeText, LongTabu
from pylatex.utils import bold

import json


if __name__ == '__main__':
    with open("data.json", "r") as f:
        data = json.load(f)
    title = "23. Neujahrssportfest des SV Werder Bremen"
    subtitle = "am 14.01.2023 in Bremen"
    geometry_options = {
        "tmargin": "15mm", "lmargin": "20mm", "rmargin": "20mm",
        "bmargin": "20mm"
    }
    doc = Document(geometry_options=geometry_options, page_numbers=False)
    doc.change_length("\\tabulinesep", "4pt")

    with doc.create(Section(title, numbering=False)):
        doc.append(MediumText(bold(subtitle)))
        doc.append(NewLine())
        doc.append(NewLine())
        # Generate data table
        with doc.create(
                LongTabu("X[2.5, l] X[1.5, l] X[r] X[1.5, r] X[r]")) as data_table:
            header_row1 = ["Name", "", "Rang", "Leistung", "SB/PB"]

            for age in data:
                data_table.add_row((MultiColumn(5, align='l',
                                                data=LargeText(bold(age))),))
                data_table.add_empty_row()
                for disc in data[age]:
                    data_table.add_row(
                        (MultiColumn(
                            5, align='l', data=MediumText(bold(disc))),)
                    )
                    data_table.add_row(header_row1, mapper=[bold])
                    data_table.add_hline()

                    for r in data[age][disc]:
                        row = [
                            r["name"], r["subtitle"], r["rank"], r["result"],
                            r["pborsb"]
                        ]
                        data_table.add_row(row)
                    data_table.add_empty_row()
                data_table.add_empty_row()
                data_table.add_empty_row()
    doc.generate_pdf('full', clean_tex=False)
