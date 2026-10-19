struct Data_601a6ec0 {
    unsigned char pad[0x1e];
    unsigned char field;
};

extern "C" int func_601a6ec0(const Data_601a6ec0 *p)
{
    return p->field != 0;
}