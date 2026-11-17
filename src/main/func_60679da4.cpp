extern "C" void func_6065ca7c(void *);
extern "C" void func_60679dc4(void *);

struct S {
    char pad0[0x38];
    short field_38;
};

extern "C" void func_60679da4(void *arg)
{
    func_6065ca7c(arg);
    func_60679dc4(arg);
    ((struct S *)arg)->field_38 = 0x16;
}