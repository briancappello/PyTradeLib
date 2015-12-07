
class Hash(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def as_dict(self):
        return self.__dict__

    def __contains__(self, item):
        return item in self.__dict__
