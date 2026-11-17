extern "C" {

void func_6056dc88(void *);
void func_6054533c(void *, int, int);

struct S {
    char pad[0x24];
    void *field_24;
};

void func_6063063c(S *s) {
    func_6056dc88(s);
    func_6054533c(s->field_24, 0x21, 0);
}

}