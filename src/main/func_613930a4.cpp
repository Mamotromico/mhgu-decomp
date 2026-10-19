struct Pair { int a; int b; };
struct Container { int header; Pair pair; };

extern "C" void func_613930a4(int *p, Container *c, Pair pair) {
    c->pair = pair;
    *p = 0;
}