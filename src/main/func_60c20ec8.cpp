struct S {
    unsigned char pad[0xF0];
    unsigned long long field;
};

extern "C" void func_60c20ec8(S* s, unsigned int a, unsigned int b)
{
    s->field = ((unsigned long long)b << 32) | a;
}