from os import listdir


class TextsSources:
    _source = './texts/'

    def __init__(self):
        self._texts = {}

        for file in listdir(self._source):
            with open(self._source + file, encoding="utf-8") as f:
                self._texts[file] = f.read()

    def __getitem__(self, item: str) -> str:
        return self._texts[item]


class TextsBuilder:
    def __init__(self, sources: TextsSources) -> None:
        self._sources = sources

    @staticmethod
    def _fill_lines(line: str, values: list[dict]) -> str:
        result = []
        for line_values in values:
            result.append(line.format(**line_values))
        return '\n'.join(result)

    def remind_about_program(self)->str:
        return self._sources['remind_about_program']

    def your_points(self, values: list[dict]) -> str:
        """ @param values: list of {'points': int, 'category': str} dicts. """
        source = self._sources['your_points']
        return self._fill_lines(line=source, values=values)

    def announce_winners(self, values: list[dict]) -> str:
        """ @param values: list of {'category': str, 'points': int, 'user': str} dicts. """
        header, line = self._sources['announce_winners'].split('\n')
        lines = self._fill_lines(line=line, values=values)
        return f'{header}\n{lines}'


texts = TextsBuilder(sources=TextsSources())
