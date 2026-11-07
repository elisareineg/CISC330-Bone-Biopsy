"""Independent reference cases: centre (0,0,0), radius 1 mm, axis +x."""

def planning_cases():
    # Literal expected values derived in docs/STAGE4_DERIVATIONS.md.
    rows = [
        ('intersects', [-5, .6, 0], .6, 1.6, 5.8, 'intersects'),
        ('tangent', [-5, 1, 0], 1., 0., 5., 'contact'),
        ('miss', [-5, 2, 0], 2., 0., None, 'miss'),
        ('behind', [5, 0, 0], 0., 0., None, 'behind'),
        ('inside', [0, 0, 0], 0., 1., 1., 'intersects'),
        ('surface_inward', [-1, 0, 0], 0., 2., 2., 'intersects'),
        ('surface_outward', [1, 0, 0], 0., 0., 0., 'contact'),
    ]
    return [{'name':name,'center':[0.,0.,0.],'radius':1.,'tip':tip,'axis':[1.,0.,0.],
             'expected':{'targeting_error_mm':error,'core_length_mm':core,
                         'insertion_depth_mm':depth,'status':status}}
            for name,tip,error,core,depth,status in rows]

# Author: Serhat Yaylacam
