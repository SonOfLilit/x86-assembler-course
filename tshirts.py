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
1mvto                 move OT to top of param stack
2mvfr                 move top of param stack to operations stack
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
for i in xrange(10):
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
        self.s = map(lambda x: [], xrange(10))
        self.s[CONST0] += [0] * 20
        self.s[INSTR] += instructions
        self.s[INSTR].reverse()
        
    def step(self):
        instruction = self.s[INSTR].pop()
        param = self.s[INSTR].pop()
        print OPNAMES[instruction]
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
    
    def show(self):
        return "\n".join(map(self.show_stack, enumerate(self.s)))
    def show_stack(self, (i, stack)):
        return "%8s [%s]" % (STACKNAMES[i], "\t".join(OPNAMES[x] for x in stack))

    def stop(self, param):
        print
        print
        print "Output:"
        print self.show_stack((9, self.s[9]))
        print "Program exited with param %d" % param
        raise DoneException()

    def mvto(self, param):
        value = self.s[OPER].pop()
        self.s[param].append(value)
    def mvfr(self, param):
        value = self.s[param].pop()
        self.s[OPER].append(value)

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
        print "*** noop with param %d" % param
    
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



def compile(string):
    string = string[string.find("=="):]
    string = re.sub(";.*", "", string)
    return map(int, filter(str.isdigit, string))

stop = compile("""
Stop
====

0stop 0stop
""")

istop = compile("""
Indirectly stop
===============

; set OT to 0const by moving a 0 from 0const to 3oper
2mvfr 0const
; exchange instruction stack with 0const stack
9exch 1instr
""")

fiveshirts = compile("""
Output 5 blue shirts
====================

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
Call a subroutine to output a blue shirt
========================================

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


s = State(locals()[sys.argv[1]])

s.loop()
