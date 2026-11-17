extern "C" unsigned func_607aef68(void *);

struct S {
    char pad[4];
    unsigned field_4;
};

extern "C" void func_613b8c9c(struct S *s, void *p)
{
    unsigned r = func_607aef68(p);
    if (s->field_4 != r)
        s->field_4 = r;
}