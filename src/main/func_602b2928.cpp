extern "C" {

struct S {
    char pad[0x3320];
    int field;
};

extern int D_6188c258;

int func_603cd308(int, int, int);

int func_602b2928(struct S *p) {
    int v = p->field;
    int a = D_6188c258;
    return func_603cd308(a, v, 2);
}

}