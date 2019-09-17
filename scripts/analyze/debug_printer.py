
"""
a mechanism for increasing and decreasing the level of indentation when printing,
particularly when entering and leaving functions; useful for debugging
(this is a class to be imported by other scripts)
"""

class debug_printer:

    DEBUG = False
    INDENTATION_SPACES = 3
    saved_states = [False]

    def __init__(self, spaces):
        self.indentation_level = 0
        self.INDENTATION_SPACES = spaces
        self.saved_states = [False]

    # functions for turning debug printout on and off and for restoring the
    # current state to either on or off, whichever it was before the most
    # recent state change
    def on(self):
        self.saved_states.append(self.DEBUG)
        self.DEBUG = True

    def off(self):
        self.saved_states.append(self.DEBUG)
        self.DEBUG = False

    def restore(self):
        if self.saved_states:
            self.DEBUG = self.saved_states.pop()
        else:
            self.DEBUG = False

    # returns a number of spaces consistent the current level of indentation
    # the -1 is because when the string is used in print(), an extra space is
    # added
    def indentation_spaces(self):
        return "".ljust(self.indentation_level * self.INDENTATION_SPACES - 1)

    # returns a string of the form 'x_1 x_2 ... x_k"
    # when given a tuple (x_1, x_2, ... , x_k)
    def tuple_to_string(self, the_tuple):
        return ' '.join([str(i) for i in the_tuple])

    # prints an appropriate message when entering a function
    # and indents one level
    # first argument is the function name
    # remaining arguments are printed as given
    def enter(self, *args):
        if self.DEBUG:
            function = args[0]
            other_info = self.tuple_to_string(args[1:])
            print(self.indentation_spaces(), "->", function, other_info)
        self.indentation_level = self.indentation_level + 1

    # prints an appropriate message when leaving a function and undoes the indentation
    # first argument is the function name
    # remaining arguments are printed as given
    def leave(self, *args):
        self.indentation_level = self.indentation_level - 1
        if self.DEBUG:
            function = args[0]
            other_info = self.tuple_to_string(args[1:])
            print(self.indentation_spaces(), "<-", function, other_info)

    # passes its arguments to print() with the appropriate indentation level
    def dprint(self, *args):
        if not self.DEBUG:
            return
        info_to_print = self.tuple_to_string(args)
        print(self.indentation_spaces(), info_to_print)

    def test(self, n):
        self.enter("test", n)
        if n % 2 == 0:
            self.off()
        else:
            self.on()
        self.dprint("test", n, "inside")
        if n > 0:
            self.test(n - 1)
        if n % 2 == 0:
            self.off()
        else:
            self.restore()
        self.leave("test", n)

if __name__ == '__main__':
    printer = debug_printer()
    printer.test(5)

#  [Last modified: 2019 09 17 at 21:39:04 GMT]
