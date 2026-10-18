struct func_6113a254_s {
    unsigned char pad[0x44];
    float value;
};

extern "C" float func_6113a254(struct func_6113a254_s *p, float a, float b)
{
    float r = a + b;
    p->value = r;
    return r;
}