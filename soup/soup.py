from .tags import Tag

class Soup:
    tags = []
    slen = 0
    _val = ''

    def _name(self,pos):
        name = ''
        for i in range(pos,self.slen):
            pc = self._val[i]
            if '' == pc.strip() or pc == '/': break
            name += pc

        return name.replace('>','').replace('<','')

    def _fd_tag_close(self,name):
        for t in reversed(self.tags):
            if t.name == name and t.close == None:
                return t

        return None

    def __init__(self, value:str):
        self._val = value
        self.slen = len(value)
        self.tags = []

        prev = ''
        for i,c in enumerate(value):
            _nxt = None if i >= (self.slen-1) else value[i+1]

            if c == '>' and prev == '<':
                del self.tags[-1]
                continue

            if c == '>' and prev == '/' and i > 2 and value[i-2] == '<':
                continue

            # if open tag
            if c == '<' and i < self.slen and _nxt != '/':
                name = value[i:self.slen].split()[0].split('>')[0]
                name = name.split('<')[-1].replace('/','')

                self.tags.append(Tag(
                    name = name ,
                    tabs = value[0:i].split('\n')[-1],
                    start = i,
                ))

            # close simple tag
            if prev == '/' and c == '>' and len(self.tags) != 0: #  />
                self.tags[-1].start_ends = i+1

            # if close a complex tag
            if c == '<' and _nxt == '/': # </
                name = self._name(x+1)
                tag  = self._fd_tag_close(name)

                if tag != None:
                    tag.close = i
                    for n in range(i+len(name),self.slen):
                        if value[n] == '>':
                            tag.close_ends = n+1
                            break

            # if close complex tag
            if prev != '/' and c == '>':
                name = '' # could be None but '' is already checked in next 'if'
                for x in reversed(range(i)):
                    pc = value[x]
                    if pc == '<':
                        name = value[x+1:self.slen].split()[0]
                        name = name.split('<')[-1].strip()
                        name = name.replace('<','').replace('>','').replace('/','')
                        break

                # end opened tag
                if '/' not in name and name.strip() != '':
                    tag = self._fd_tag_close(name)
                    if tag != None:
                        tag.close_ends = i+1

            prev = c

        for t in self.tags:
            t.save_tags(value)

    def apply(self,args:dict,cbfn):
        for t in self.tags:
            good = True
            for k,v in args.items():
                a = getattr(t,k,None)
                if v != a:
                    good = False
                    break
            if good:
                cbfn(t)
        return self

    def find_by(self,**kwargs):
        arr = []

        attrs = {}
        if 'attrs' in kwargs:
            attrs = kwargs['attrs']
            del kwargs['attrs']

        has_attrs = len(list(attrs.keys())) != 0

        for t in self.tags:
            append = True

            for k,v in kwargs.items():
                a = getattr(t,k,None)
                if v != a:
                    append = False
                    break

            if has_attrs and append:
                links = t._load_attrs()
                for a in attrs.keys():
                    if a not in links:
                        append = False
                        break
                    if attrs[a] != links[a]:
                        append = False
                        break

            if append:
                arr.append(t)

        return arr

    def to_string(self):
        nv = ''

        reach = 0
        for t in self.tags:
            s,e = t.outer_pos()
            if not t.has_changes():
                continue

            if s < reach:
                continue

            nv += self._val[reach:s]
            nv += t.render()

            reach = e

        nv += self._val[reach:self.slen]
        return nv
