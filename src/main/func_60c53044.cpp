#include <stdint.h>

struct func_60c53044_obj {
    uint32_t pad0[48];
    uint32_t field_c0;
    uint32_t pad1[12];
    uint32_t field_f4;
};

extern "C" void func_60c53044(struct func_60c53044_obj *obj)
{
    obj->field_f4 = obj->field_c0;
}