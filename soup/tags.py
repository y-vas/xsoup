from functools import cache

class Tag:
    name       = ''
    tabs       = ''
    start      = 0
    start_ends = None
    close      = None
    close_ends = None

    _attrs = {}
    _contents  = None
    _start_tag = ''
    _close_tag = ''

    _link = None
    _replace = None

    def __init__(self,
        name       = '',
        tabs       = '',
        start      = 0,
        start_ends = None,
        close      = None,
        close_ends = None
    ):

        self.name       = name
        self.tabs       = tabs
        self.start      = start
        self.start_ends = start_ends
        self.close      = close
        self.close_ends = close_ends
        self._attrs     = {}
        self._refs      = {}

    def is_ref(self):
        return self.name == 'ref'

    def is_attr_true(self,attr):
        attrs = self._load_attrs()
        return attrs.get(attr,False) == True


    def save_tags(self,value):
        self._start_tag = value[self.start:self.start_ends]

        if self.close_ends is None:
            self._contents = value[self.start:self.start_ends]
            self._close_tag = ''
            return

        self._close_tag = value[self.close:self.close_ends]
        self._contents = value[self.start:self.close_ends]

        attrs = self._load_attrs_no_cache()
        for key, value in attrs.items():
            if key.startswith(':'):
                pass

    def outer(self):
        return self._contents

    def outer_pos(self):
        if self.close_ends is None:
            return [self.start,self.start_ends]
        return [self.start,self.close_ends]

    @cache
    def _load_attrs(self):
        return self._load_attrs_no_cache()

    def _load_attrs_no_cache(self):
        # tne = tag name end
        tne = self._start_tag.find(' ')
        if tne == -1:
            tne = self._start_tag.find('>')

        tag_name = self._start_tag[1:tne]
        remaining_tag = self._start_tag[tne + 1:]
        while remaining_tag:
            attr_end = remaining_tag.find('=')
            if attr_end == -1:
                attr_name = remaining_tag.strip()

                if '"' in attr_name:
                    break

                nn = attr_name.split()
                if len(nn) == 0:
                    break

                attr_name = nn[0]
                self._attrs[attr_name] = True
                break

            attr_name = remaining_tag[:attr_end].strip()
            remaining_tag = remaining_tag[attr_end + 1:]

            quote_char = remaining_tag[0]
            attr_value_end = remaining_tag.find(quote_char, 1)
            attr_value = remaining_tag[1:attr_value_end]
            remaining_tag = remaining_tag[attr_value_end + 1:].strip()

            if '"' in attr_name or '"' in attr_value:
                continue

            self._attrs[attr_name] = attr_value

        return self._attrs

    def match(self,**kwargs):
        for k,v in kwargs.items():
            if getattr(self,k) != v:
                return False

        return True

    def get_attr(self,attr,defaults_to=None):
        attrs = self._load_attrs()
        return attrs.get(attr,defaults_to)

    def get_paths(self):
        if self._link is not None:
            return self._link

        path = self.get_attr('link')

        if path is None:
            return None

        path = path.split('/')

        self._link = {
            'name' : path[0],
            'path' : path[1:]
        }

        return self._link

    def set_replace(self,v):
        self._replace = v

    def __repr__(self):
        posi = [ self.start,self.start_ends,self.close,self.close_ends ]
        poss = ",".join([ str(x) for x in posi if x != None ])
        return f"<{self.name} pos='{poss}' />"

    def _render_counter(self):
        series = self.get_attr( 'series' )
        if series is None:
            return str(self._replace)

        if str(series).isnumeric() and str(self._replace).isnumeric():
            s = int(series)
            n = int(self._replace)

            return str(int(n % s))

        return str(self._replace)

    def render( self ):
        if not self.has_changes():
            return self.outer()

        if self.name == 'counter':
            return self._render_counter()

        elif self.is_ref():
            if self.get_attr('ignore-spaces') != None:
                return str(self._replace)

            return f"\n{self.tabs}".join(
                str(self._replace).split('\n')
            )

        return str(self._replace)

    def has_changes(self):
        return self._replace != None
