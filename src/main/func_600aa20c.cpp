struct S_600aa20c {
    unsigned char pad[0x7580];
    unsigned char field;
};

extern "C" void func_600aa20c(S_600aa20c *p) {
    p->field = 2;
}