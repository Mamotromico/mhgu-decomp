struct S { unsigned char pad[0x38]; unsigned char field; };
extern "C" int func_6080c93c(S *self) {
    unsigned char x = self->field;
    x--;
    return x < 26;
}
