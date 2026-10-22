struct s601ba73c {
    unsigned char pad0[4];
    unsigned short field4;
    unsigned char field6;
};

extern "C" void func_601ba73c(s601ba73c *p) {
    p->field4 = 0;
    p->field6 = 5;
}