struct S_6135359c {
    char pad[0xC];
    unsigned short field;
};

extern "C" void func_6135359c(int *p0, S_6135359c *p1, unsigned short value) {
    p1->field = value;
    *p0 = 0;
}