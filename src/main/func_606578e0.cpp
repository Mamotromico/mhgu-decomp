extern "C" void func_6056dc28(void *p);

struct S60 {
    char pad[0x54];
    int field_54;
};

extern "C" void func_606578e0(struct S60 *p)
{
    func_6056dc28(p);
    p->field_54 = -1;
}