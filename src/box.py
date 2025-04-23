class Box:
    def __init__(self, x, y, x2=None, y2=None, w=0.0, h=0.0, uuid=None, l=0):
        self.uuid = uuid
        self.l = l
        self.keep = True

        self.x = x
        if x2 is None:
            self.w = w
            self.x2 = self.x + self.w
        else:
            self.x2 = x2
            self.w = self.x2 - self.x

        self.y = y
        if y2 is None:
            self.h = h
            self.y2 = self.y + self.h
        else:
            self.y2 = y2
            self.h = self.y2 - self.y

    def __getitem__(self, index):
        return [self.x, self.y, self.x2, self.y2][index]

    def __eq__(self, b2):
        assert type(b2) is Box

        intersection = Box(
            x=max(self[0], b2[0]),
            y=max(self[1], b2[1]),
            x2=min(self[2], b2[2]),
            y2=min(self[3], b2[3]),
        )
        return intersection

    def __add__(self, other):
        return float(self) + float(other)

    def __radd__(self, other):
        return float(self) + float(other)

    def __sub__(self, other):
        return float(self) - float(other)

    def __rsub__(self, other):
        return float(other) - float(self)

    def __truediv__(self, other):
        return float(self) / float(other)

    def __lt__(self, other):
        return float(self) < float(other)

    def area(self) -> float:
        return float(max(self.h, 0) * max(self.w, 0))

    def iou(self, boxb) -> float:
        if self.l != boxb.l:
            return 0.0

        intersection = self == boxb

        if intersection.area() == 0:
            return 0.0

        else:
            union = self + boxb - intersection
            return intersection / union

    def __float__(self):
        return self.area()
