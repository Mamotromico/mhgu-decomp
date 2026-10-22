extern "C" {
struct S {
    char pad[0x6c];
    struct S *field_6c;
    struct S *field_70;
};

void func_60a4844c(struct S *a, struct S *b) {
    a->field_6c = b;
    if (b) {
        b->field_70 = a->field_70;
    }
}
}