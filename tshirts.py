"""
One question that occupies me very much is "what should be in the first lesson".

However we decide to recruit people for the group, it is quite obvious
that the first lesson will decide who wants to stay and who doesn't.
More importantly, it will decide how they will feel about the subject
- how much fun they'll see in it. On one hand, I'd rather they not
form the opinion that it's "too hard for them" and "they're not cut
for it" (which is hard when teaching assembly language), and on the
other, I was surprised to hear from many friends that their favourite
teachers were those that really hit them hard in the first lesson of
the subject.

It will have to include some form of introduction (of the subject and
of the personae dramatis). For subject I'm thinking of showing some
demoscene demos [1]. Not those of the "short code" tradition, since I
can't explain why short code is interesting without... yup, teaching
assembly language, but of the awesome effects tradition [2]. I'll also
have to talk a little bit about where it's useful in the real world -
embedded, debugging, anti-debugging, compilers, security,
vulnerability research, people earning loads of money [3].

It will also have to include an actual taste of assembly language
programming. I've been entertaining two options:

1) Teach bits, then binary numbers, then a whole lesson in
bit-twiddling tricks [4]

2) Teach about data representations (perhaps give them an ASCII table
and ask them to write a message, then shuffle all the papers and deal
randomly, then let them decode each other's messages), then about a
simple computing machine with code-data duality, then show all kinds
of awesome tricks that can be done when you have code-data duality.

I've been considering this narrative:


My uncle has a T-shirt factory. He produces shirts in ten different
colors.

There used to be two workers, an old couple: he sews the shirts, puts
them in a tall laundry basket, puts the laundry basket by his wife's
desk, she takes shirts from the basket, colors the shirts, sorts them
in boxes according to different customers' orders and ships them off.
For example she might need to make a whole box of white shirts for a
school, or a box full of
blue-shirt-yellow-shirt-blue-shirt-yellow-shirt for a sports club's
fan club.

The business went well, and the years flew by, until one day the old
lady decided she wants to spend more time with her grandchildren and
resigned. As a parting gift, she had her daughter the engineer make a
machine to replace her.

The machine was built to be generic, and since there was paper
shortage in the factory, it accepts instructions as T-shirts.


Color code (resistor colors with black and white inverted):

0 (White)
1 (Brown)
2 (Red)
3 (Orange)
4 (Yellow)
5 (Green)
6 (Blue)
7 (Violet)
8 (Gray)
9 (Black)

Stack special roles:

0 - constant 0      - has a large supply of white shirts

1 - instruction     - instructions are read from here

2 - recycle         - used instructions are discarded here

3 - operations      - the top of this stack, referred subsequently as OT,
                      is a parameter in many operations

4 - garbage         - we throw garbage here (only semantic role)

9 - output          - when the machine stops, output is expected to be here


Opcodes (each receives a parameter, unless noted as "immediate" the
param represents the stack to operate upon):

0stop                 stop. It is customary to give 0stop as parameter
1mvto                 move OT to top of param stack (if it's empty, do nothing)
2mvfr                 move from param stack to operations (if empty, do nothing)
3addi                 OT <- OT + param (as immediate, not stack number)
4muli                 OT <- OT * param (as immediate)
5adds                 top of param stack <- top of param stack + OT*
6muls                 top of param stack <- top of param stack * OT*
7noop                 does nothing (for debugging, prints argument)
8flip                 flip param stack**
9exch                 exchange param stack with stack indicated by OT**


* since the implementation in hardware is "pop top of param stack,
  color it, push it", if param stack is 3oper, it performs the
  operation with the shirt /below/ OT. E.g., if 3oper had "7 2" and
  5adds 3oper was executed, 3oper would now be "7 9"

** used instructions are thrown into 2recycle after the operation is
   performed


There are some example programs below in the code.


[1] http://pouet.net/prodlist.php?platform[]=Windows&type[]=demo&order=views
[2] https://www.youtube.com/watch?v=wTXqVllK3IM&feature=related,
https://www.youtube.com/watch?v=u1n8uYmi9W8&feature=related
[3] I'm a bit against mentioning that, but it sounds like it is very
relevant to my crowd
[4] http://graphics.stanford.edu/~seander/bithacks.html#IntegerMinOrMax
"""
import sys
import operator
import re


NUM_STACKS = 10

COLORS = [
    "0white",
    "1brown",
    "2red",
    "3orange",
    "4yellow",
    "5green",
    "6blue",
    "7violet",
    "8gray",
    "9black"
    ]
STACKS = [
    "0const",
    "1instr",
    "2recycle",
    "3oper",
    "4garbage",
    "5stack",
    "6stack",
    "7stack",
    "8stack",
    "9out"
    ]
OPERATORS = [
    "0stop",
    "1mvto",
    "2mvfr",
    "3addi",
    "4muli",
    "5adds",
    "6muls",
    "7noop",
    "8flip",
    "9exch"
    ]
NUMBERS = {}
for i in xrange(NUM_STACKS):
    NUMBERS[COLORS[i]] = i
    NUMBERS[STACKS[i]] = i
    NUMBERS[OPERATORS[i]] = i
del i
OPNAMES = dict(enumerate(OPERATORS))
STACKNAMES = dict(enumerate(STACKS))

CONST0 = 0
INSTR = 1
RECYCLE = 2
OPER = 3

class DoneException(Exception):
    pass

class State(object):
    def __init__(self, instructions):
        self.s = map(lambda x: [], xrange(NUM_STACKS))
        self.s[CONST0] += [0] * 1000
        self.s[INSTR] += instructions
        self.s[INSTR].reverse()
        
    def step(self):
        instruction = self.s[INSTR].pop()
        param = self.s[INSTR].pop()
        self.output("%s %s" % (OPNAMES[instruction], param))
        self.ops[instruction](self, param)
        self.s[RECYCLE].append(instruction)
        self.s[RECYCLE].append(param)
    
    def loop(self):
        try:
            while True:
                print self.show()
                self.step()
#                raw_input()
                print
        except DoneException:
            pass
    
    def output(self, message):
        print message

    def show(self):
        return "\n".join(map(self.show_stack, enumerate(self.s)))
    def show_stack(self, (i, stack)):
        return "%8s [%s]" % (STACKNAMES[i], "\t".join(OPNAMES[x] for x in stack))

    def stop(self, param):
        self.output("Program exited with param %d" % param)
        raise DoneException()

    def mvto(self, param):
        self.mvfrto(OPER, param)
    def mvfr(self, param):
        self.mvfrto(param, OPER)
    def mvfrto(self, fr, to):
        if self.s[fr]:
            value = self.s[fr].pop()
            self.s[to].append(value)

    def addi(self, param):
        self.op_i(operator.add, param)
    def muli(self, param):
        self.op_i(operator.mul, param)
    def op_i(self, op, param):
        self.s[OPER][-1] = (op(self.s[OPER][-1], param)) % 10

    def adds(self, param):
        self.op_s(operator.add, param)
    def muls(self, param):
        self.op_s(operator.mul, param)
    def op_s(self, op, param):
        a = self.s[param].pop()
        b = self.s[OPER][-1]
        r = op(a, b) % 10
        self.s[param].append(r)

    def noop(self, param):
        self.output("*** noop with param %d" % param)
    
    def flip(self, param):
        self.s[param].reverse()
    def exch(self, param):
        param2 = self.s[OPER][-1]
        self.s[param], self.s[param2] = self.s[param2], self.s[param]
    
    ops = [
        stop,
        mvto,
        mvfr,
        addi,
        muli,
        adds,
        muls,
        noop,
        flip,
        exch
        ]


import curses

class CursedState(State):
    STACK_WIDTH = 10
    
    def loop(self):
        def f(stdscr):
            self.stdscr = stdscr
            assert curses.COLOR_PAIRS >= NUM_STACKS + 1
            """
            "0white",
            "1brown",
            "2red",
            "3orange",
            "4yellow",
            "5green",
            "6blue",
            "7violet",
            "8gray",
            "9black"
            """
            self.colors = {
                # since 0 can't be modified
                0: curses.color_pair(11),
                1: curses.color_pair(1),
                2: curses.color_pair(2),
                3: curses.color_pair(3),
                4: curses.color_pair(4),
                5: curses.color_pair(5),
                6: curses.color_pair(6),
                7: curses.color_pair(7),
                8: curses.color_pair(8),
                9: curses.color_pair(9)
                }
            curses.init_pair(11, 0, 7)
            curses.init_pair(1, 3, 1)
            curses.init_pair(2, 0, 1)
            curses.init_pair(3, 1, 3)
            curses.init_pair(4, 0, 3)
            curses.init_pair(5, 0, 2)
            curses.init_pair(6, 0, 4)
            curses.init_pair(7, 0, 5)
            curses.init_pair(8, 0, 6)
            curses.init_pair(9, 7, 0)

            self.initial_stacks = map(list, self.s)
            self.stepping = True
            self.ff_target = None
            self.step_count = 0
            self.separate_couples = True
            self.message = ""
            
            self.show()
            try:
                while True:
                    self.step_count += 1
                    if self.step_count == self.ff_target:
                        self.stepping = True
                    self.message = "%r\t" % (self.step_count)
                    self.step()
                    if self.stepping:
                        self.show()
            except DoneException, e:
                self.show()
            except object, e:
                self.message = str(e)
                self.show()
            
        curses.wrapper(f)

    def output(self, message):
        self.message += message + "\t"

    def show(self):
        self.stdscr.clear()
        self.stdscr.addstr(0, self.STACK_WIDTH * NUM_STACKS / 2,
                           self.message, curses.A_STANDOUT)
        my, mx = self.stdscr.getmaxyx()
        for (i, stack) in enumerate(self.s):
            self.show_stack(my, mx, i, stack)
        self.prompt()

    def prompt(self):
        self.stdscr.refresh()
        while True:
            c = self.stdscr.getch()
            # forward
            if c == ord(' '):
                break
            # back
            if c == ord('b'):
                self.goto(self.step_count - 1)
                break
            # goto
            if c == ord('g'):
                self.goto(int(self.stdscr.getstr(1, 10)))
                break
            # separator
            if c == ord('s'):
                self.separate_couples = not self.separate_couples
                self.show()
                break
            # refresh
            if c == ord('r'):
                self.show()
                break
            # guess...
            if c == ord('q'):
                sys.exit(0)

    def goto(self, i):
        self.ff_target = i

        if i < self.step_count:
            self.s = map(list, self.initial_stacks)
            self.step_count = 0

        if self.ff_target > self.step_count:
            self.stepping = False

    def show_stack(self, my, mx, i, stack):
        self.stdscr.addstr(my-1, i * self.STACK_WIDTH, STACKNAMES[i], self.colors[i])
        
        for j, instruction in enumerate(stack):
            y = my - 3 - j
            if self.separate_couples:
                y -= j/2
            if y > 1:
                self.stdscr.addstr(y, i * self.STACK_WIDTH, OPNAMES[instruction], self.colors[instruction])
            else:
                self.stdscr.addstr(1, i * self.STACK_WIDTH, "...")
                
            

    

def compile(string):
    string = re.sub(";.*", "", string)
    return map(int, filter(str.isdigit, string))

stop = compile("""
;Stop
;====

0stop 0stop
""")

istop = compile("""
;Indirectly stop
;===============

; set OT to 0const by moving a 0 from 0const to 3oper
2mvfr 0const
; exchange instruction stack with 0const stack
9exch 1instr
""")

fiveshirts = compile("""
;Output 5 blue shirts
;====================

2mvfr 0const
3addi 6blue

5adds 0const
2mvfr 0const
1mvto 9out
5adds 0const
2mvfr 0const
1mvto 9out
5adds 0const
2mvfr 0const
1mvto 9out
5adds 0const
2mvfr 0const
1mvto 9out
5adds 0const
2mvfr 0const
1mvto 9out
0stop 0stop
""")


subroutine = compile("""
;Call a subroutine to output a blue shirt
;========================================

;; make a subroutine that outputs a blue shirt and returns to us

;; store it in 7stack (so on being called it has to exchange stacks
;; 2recycle and 7stack, then to return it has to flip 7stack and
;; exchange 1instr and 7stack)

;; place the subroutine in 3oper

;;;;;;;;; Subroutine: Output a blue shirt
;;;;; we can assume that OT is 7 since we got called
;;;; 9exch 2recycle
2mvfr 1instr
9exch
2mvfr 1instr
2recycle
;;;;; do what we're meant to
;;;; 2mvfr 0const
;;;; 3addi 6blue
;;;; 1mvto 9out
2mvfr 1instr
2mvfr
2mvfr 1instr
0const
2mvfr 1instr
3addi
2mvfr 1instr
6blue
2mvfr 1instr
1mvto
2mvfr 1instr
9out
;;;;; return
;;;; 8flip 7stack
;;;;; OT is 7 from before
;;;; 9exch 1instr
2mvfr 1instr
8flip
2mvfr 1instr
7stack

;; nop 3
2mvfr 1instr
7noop
2mvfr 1instr
3

2mvfr 1instr
9exch
2mvfr 1instr
1instr
;; it is now upside-down. flip it (could have been avoided but then
;; would be less readable)
8flip 3oper

7noop 1

;; move it, with an extra 7, to 7stack
2mvfr 1instr
7stack
9exch 3oper

;; move the 7 back to 3oper
2mvfr 7stack

;; put "0stop 0stop" in 6stack, will be useful later
2mvfr 0const
1mvto 6stack
2mvfr 0const
1mvto 6stack

;; clean 2recycle, so that when we call the subroutine it will return
;; to just after we clean it

;; OT 7 is now 8
3addi 1
9exch 2recycle

;; OT 8 back to 7
3addi 9
;; and, call!
9exch 1instr

;; notice that when we're called back, we'll immediately switch to
;; 6stack. So we put code there to stop the program.
""")


infinite_loop = compile("""
;Infinite loop that outputs blue shirts
;======================================

;; Big picture:

; We'll use stacks 0-4 and 9 as intended and also 7stack for temporary
; storage*.
;
; We're going to use a "reflector" - a piece of code that returns
; control right back to what's in the recycle bin.  A reflector
; requires handling with care. When we get control back, we have the
; reflector itself in the recycle bin that must be disposed of (or
; else on the next iterator the reflector will return control to
; <reflector|our code>).
;
; When the reflector returns control to us, there is always 7stack in
; OT. That is because it has to do 9exch 1instr to return control. It
; is actually useful - we could 0exch 2recycle and then put the
; reflector in the 4garbage without worrying about our own code
; muddling 2recycle. But to do that we need to make sure we have a 7
; in OT on the first run, and clean up the code that creates that 7
; from 2recycle so that it would indeed only happen in the first
; run.
;
; Note: there are two approaches: Either we find some way to preserve
; our reflector out of harm's way, or we throw it in the garbage and
; create a new one in each iteration. Here we've chosen the second way.
; See in git for an implementation using the first way (which is much
; more complex but I found it first).
;
; 
; Note2: The reader is strongly advised to follow this code's evolution
; in git.
;
;
; * At one point it this code's life, it *had* to be 7stack for our
;   code to work: I had to switch stacks 1 and 7, and it left a 7 on
;   the bottom of 3oper that I couldn't remove, and it would've put
;   the next reflector I built out of sync! The elegant solution was
;   to add an extra 7, making them a noop command that would execute
;   harmlessly before the reflector.


;; make a "reflector" that re-runs all code (which outputs then calls
;; the reflector, ...) when called. Store it in 7stack (so on being
;; called it has to immediately exchange stacks 2recycle and 7stack to
;; avoid adding things to our code in 2recycle, then to return it has
;; to flip 7stack and exchange 1instr and 7stack)

;; build the subroutine in 3oper

;;;;;;;;; Subroutine: Rerun us
;;;;; we can assume that OT is 7 since we got called
;;;; 9exch 2recycle
;;;;; return
;;;; 8flip 7stack
;;;;; OT is 7 from before
;;;; 9exch 1instr
2mvfr 0const
3addi     9exch
2mvfr 0const
3addi     2recycle
2mvfr 0const
3addi     8flip
2mvfr 0const
3addi     7stack
2mvfr 0const
3addi     9exch
2mvfr 0const
3addi     1instr
; it must be flipped before it can run. We do that later.

;; move it to 7stack
2mvfr 0const
3addi 7
9exch 3oper

;; move the 7 in OT back to 3oper
2mvfr 7stack

;; clean 2recycle
;;   7 + 7 = 4garbage
3addi 7
;; This is the first code that runs in a subsequent iteration, upon
;; which it puts the reflector in stack 7
9exch 2recycle

;; flip the reflector so it can run again
8flip 7stack

;; output a blue shirt

;; there is a spare 7 on the stack, add 9 and you get 6blue
3addi 9
1mvto 9out

2mvfr 0const
3addi 7stack

;; and, call!
9exch 1instr
""")


s = CursedState(locals()[sys.argv[1]])

s.loop()
