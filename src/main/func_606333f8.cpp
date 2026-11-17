extern "C" int func_6056dc28(void *);
extern "C" int func_6054533c(void *, int, int);

struct S {
    char pad[0x24];
    void *field_24;
};

extern "C" int func_606333f8(S *s)
{
    func_6056dc28(s);
    return func_6054533c(s->field_24, 0x64, 1);
}