from pylatex import Document, Section, MultiColumn, NewLine, \
    MediumText, LargeText, LongTabu, NoEscape, Package, LongTable
from pylatex.utils import bold


def make_pdf(data, title, subtitle, name="main"):


    geometry_options = {
        "tmargin": "15mm", "lmargin": "20mm", "rmargin": "20mm",
        "bmargin": "20mm"
    }
    doc = Document(geometry_options=geometry_options, page_numbers=False)
    doc.change_length("\\tabulinesep", "4pt")
    doc.packages.append(Package("xcolor"))
    # remove dependency of Package("longtable") from LongTabu
    # and add longtable[_v4.13] to the preambel for compatibility
    # purposes
    LongTabu.packages = [Package("tabu")]
    doc.preamble.append(NoEscape(r'\usepackage{longtable}[=v4.13]'))
    with doc.create(Section(title, numbering=False)):
        doc.append(MediumText(bold(subtitle)))
        doc.append(NewLine())
        doc.append(NewLine())
        # Generate data table
        fmt_string = r"\hspace*{-1mm}\colorbox{black!10}{\strut\parbox{\dimexpr\textwidth - 2\fboxsep\relax}{"
        with doc.create(
                LongTabu(
                    "X[2.5, l] X[1.5, l] X[r] X[1.5, r] X[r]")) as data_table:
            header_row1 = ["Name", "", "Rang", "Leistung", "SB/PB"]
            row_counter = 0
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
                        if row_counter % 2:
                            row = [
                                NoEscape(fmt_string + r["name"] + r"}}"),
                                r["subtitle"], r["rank"], r["result"],
                                r["pborsb"]
                            ]
                        else:
                            row = [r["name"], r["subtitle"], r["rank"],
                                   r["result"], r["pborsb"]
                                   ]
                        data_table.add_row(row)
                        row_counter += 1
                    data_table.add_empty_row()
                data_table.add_empty_row()
                data_table.add_empty_row()
    doc.generate_pdf(name, clean_tex=True)


if __name__ == '__main__':
    make_pdf([], "", "")
