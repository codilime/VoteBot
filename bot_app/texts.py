from os import listdir


class TextsSources:
    """ On app's startup loads all predefined texts that can be later sent to users in messages. """
    _source = './bot_app/texts/'

    def __init__(self):
        self._texts = {}

        for file in listdir(self._source):
            with open(self._source + file, encoding="utf-8") as f:
                self._texts[file] = f.read()

    def __getitem__(self, item: str) -> str:
        return self._texts[item]


class TextsBuilder:
    """ Using predefined templates builds texts that will be sent to users. """

    def __init__(self, sources: TextsSources) -> None:
        self._sources = sources

    @staticmethod
    def _fill_lines(line: str, values: list[dict]) -> str:
        result = []
        for line_values in values:
            result.append(line.format(**line_values))
        return '\n'.join(result)

    def greeting(self, name: str) -> str:
        return self._sources['greeting'].format(user=name)

    def about(self) -> str:
        return self._sources['about']

    def remind_about_program(self) -> str:
        return self._sources['remind_about_program']

    def your_points(self, values: list[dict]) -> str:
        """ @param values: list of {'points': int, 'category': str} dicts. """
        source = self._sources['your_points']
        return self._fill_lines(line=source, values=values)

    def your_vote(self, values: dict) -> str:
        """ @param values: {'user": str, "points": [{'category': str, 'points': int, 'user': str}]} dict. """
        header = self._sources['your_votes_header']
        line = self._sources['points_in_category']

        header = header.format(user=values['user'])
        lines = self._fill_lines(line=line, values=values['points'])
        return f'{header}\n{lines}'

    def got_voted(self, values: dict) -> str:
        """ @param values: {'people": int, "points": [{'category': str, 'points': int}]} dict. """
        header = self._sources['got_voted']
        line = self._sources['points_in_category']

        header = header.format(people=values['people'])
        lines = self._fill_lines(line=line, values=values['points'])
        return f'{header}\n{lines}'

    def announce_winners(self, values: list[dict]) -> str:
        """ @param values: list of {'category': str, 'points': int, 'users': list[str]} dicts. """
        header = self._sources['winners_header']
        line = self._sources['winners_line']
        draw = self._sources['winners_draw']

        result = []
        for line_values in values:
            is_draw = True if len(line_values['user']) > 1 else False
            line_values['user'] = ', '.join(line_values['user'])

            if is_draw:
                result.append(draw.format(**line_values))
            else:
                result.append(line.format(**line_values))

        lines = '\n'.join(result)
        return f'{header}\n{lines}'

    def you_have_not_voted(self) -> str:
        return self._sources['you_have_not_voted']

    def no_permissions(self) -> str:
        return self._sources['no_permissions']


texts = TextsBuilder(sources=TextsSources())
